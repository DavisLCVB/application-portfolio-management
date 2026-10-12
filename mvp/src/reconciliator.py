"""
Reconciliador Semántico (Semantic Reconciliator).

Este módulo implementa el Agente 3 del pipeline de descubrimiento continuo:
resuelve la brecha ontológica y nominal entre los artefactos técnicos (repositorios,
código, manifiestos) y los documentos legales/contractuales (Dark Data: TDRs).
Calcula un score heurístico de confianza multivariable (0.0 a 1.0, aún sin calibrar
contra un conjunto verificado de aplicaciones) y sintetiza una
HipotesisFactSheet compatible con LeanIX v4 y principios OCDE.
"""

import difflib
import re
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from . import config
from .connectors.spreadsheet_connector import SpreadsheetConnector, _normalize_text
from .models import (
    AplicacionCatalogo,
    CandidatoHuerfano,
    EvidenciaContractual,
    EvidenciaTecnica,
    HipotesisAnclada,
    HipotesisFactSheet,
    ResultadoReconciliacion,
)


class SemanticReconciliator:
    """
    Agente que realiza Entity Resolution y reconciliación léxico-semántica
    entre la verdad técnica del código y las obligaciones contractuales.
    """

    STOPWORDS: Set[str] = {
        "repo", "svc", "service", "servicio", "de", "del", "la", "el", "los", "las",
        "para", "por", "en", "un", "una", "tdr", "contrato", "sistema", "plataforma",
        "digital", "web", "app", "aplicacion", "portal", "modulo", "mef", "terminos", "referencia"
    }

    def __init__(
        self,
        review_threshold: float = config.REVIEW_THRESHOLD,
        min_link_score: float = config.MIN_LINK_SCORE,
    ):
        self.review_threshold = review_threshold
        self.min_link_score = min_link_score

    def calculate_name_similarity(self, tech_name: str, contract_name: str) -> float:
        """
        Calcula la similitud de nombres combinando SequenceMatcher, Jaccard y Containment.
        """
        tokens_tech = self._tokenize(tech_name)
        tokens_contract = self._tokenize(contract_name)

        if not tokens_tech or not tokens_contract:
            return 0.0

        # Similitud de Jaccard sobre tokens clave
        intersection = tokens_tech.intersection(tokens_contract)
        union = tokens_tech.union(tokens_contract)
        jaccard = len(intersection) / len(union) if union else 0.0

        # Containment / Overlap: qué porcentaje de los tokens de la app técnica están presentes en el TDR
        containment = len(intersection) / len(tokens_tech) if tokens_tech else 0.0

        # SequenceMatcher sobre strings limpios
        str_tech = " ".join(sorted(tokens_tech))
        str_contract = " ".join(sorted(tokens_contract))
        seq_ratio = difflib.SequenceMatcher(None, str_tech, str_contract).ratio()

        # Si los tokens clave de la aplicación están contenidos en el objeto del contrato, dar alto peso
        return round((0.60 * containment) + (0.20 * jaccard) + (0.20 * seq_ratio), 4)

    def calculate_tech_consistency(self, tech: EvidenciaTecnica, contract: EvidenciaContractual) -> float:
        """
        Evalúa si las tecnologías detectadas en el repositorio (lenguaje, runtime, dependencias)
        coinciden con las licencias y tecnologías estipuladas en el contrato.
        """
        if not contract.acquired_licenses:
            return 0.5  # Neutral si el contrato no especificaba licencias

        matched = 0
        total = len(contract.acquired_licenses)

        # Crear bolsa de términos técnicos del repositorio
        tech_bag = set()
        tech_bag.add(tech.primary_language.lower())
        tech_bag.add(tech.runtime_version.lower())
        for dep in tech.dependencies:
            tech_bag.add(dep.lower())
            for part in re.split(r"[-_:\.]", dep.lower()):
                if len(part) > 2:
                    tech_bag.add(part)

        for lic in contract.acquired_licenses:
            lic_clean = lic.lower()
            # Búsqueda directa o por subcadenas
            if any(lic_clean in t or t in lic_clean for t in tech_bag):
                matched += 1

        return round(matched / total, 4) if total > 0 else 0.5

    def calculate_domain_consistency(self, tech: EvidenciaTecnica, contract: EvidenciaContractual) -> float:
        """
        Evalúa la consistencia de dominio examinando si los endpoints o paquetes
        mencionan términos del objeto contractual.
        """
        contract_tokens = self._tokenize(contract.doc_name)
        if not contract_tokens:
            return 0.5

        domain_hits = 0
        total_checks = 0

        # Evaluar endpoints
        for ep in tech.endpoints:
            total_checks += 1
            ep_tokens = self._tokenize(ep)
            if ep_tokens.intersection(contract_tokens):
                domain_hits += 1

        if total_checks == 0:
            return 0.7  # Valor razonable si no hay endpoints inspeccionados

        score = domain_hits / total_checks
        return round(min(1.0, 0.4 + score), 4)

    def compute_confidence(self, tech: EvidenciaTecnica, contract: EvidenciaContractual) -> float:
        """
        Calcula el score heurístico de confianza ponderado multivariable.
        Formula: 50% similitud nominal + 35% congruencia técnica + 15% dominio.
        """
        name_sim = self.calculate_name_similarity(tech.repo_name, contract.doc_name)
        tech_sim = self.calculate_tech_consistency(tech, contract)
        domain_sim = self.calculate_domain_consistency(tech, contract)

        final_score = (0.50 * name_sim) + (0.35 * tech_sim) + (0.15 * domain_sim)
        return round(min(1.0, max(0.0, final_score)), 3)

    def reconcile_pair(self, tech: EvidenciaTecnica, contract: EvidenciaContractual) -> HipotesisFactSheet:
        """
        Genera una HipotesisFactSheet reconciliando una pareja de evidencia técnica y contractual.
        """
        score = self.compute_confidence(tech, contract)

        # Determinar nombre formal de la entidad
        # Si la similitud es alta, preferir el nombre formal del contrato/TDR
        if score >= self.min_link_score and contract.doc_name:
            entity_name = contract.doc_name
        else:
            entity_name = tech.repo_name.replace("-", " ").title()

        status = "Draft" if score >= self.review_threshold else "Requires_Verification"

        # Consolidar citas primarias (Principio OCDE 1.3)
        primary_citations = self._tech_citations(tech) + self._contract_citations(contract)

        return HipotesisFactSheet(
            entity_name=entity_name,
            candidate_type="Application",
            technical_stack=f"{tech.primary_language} ({tech.runtime_version})",
            provider=contract.provider_name,
            sla_uptime=contract.sla_uptime,
            confidence_score=score,
            status=status,
            primary_citations=primary_citations,
            business_owner=None,  # Requiere Micro-nudge
            technical_owner=tech.top_contributor,
            technical_owner_suggested=True,  # Inferido de commits: solo sugerencia
            description=f"Hipótesis generada automáticamente correlacionando el repositorio '{tech.repo_name}' con el documento '{contract.doc_id}'.",
        )

    def match_all(
        self,
        tech_list: List[EvidenciaTecnica],
        contract_list: List[EvidenciaContractual],
    ) -> ResultadoReconciliacion:
        """
        Vincula evidencias técnicas y contractuales en relación N:M.

        No es un emparejamiento uno a uno: cada par con score mayor o igual al
        score mínimo de vinculación (`min_link_score`) produce un vínculo, de modo
        que un contrato puede cubrir varios repositorios y un repositorio varios
        contratos. Las evidencias sin ningún vínculo se reportan como candidatos
        huérfanos en lugar de forzarse a la mejor coincidencia disponible.
        """
        result = ResultadoReconciliacion()
        best_tech: Dict[int, float] = {id(t): 0.0 for t in tech_list}
        best_contract: Dict[int, float] = {id(c): 0.0 for c in contract_list}
        linked: Set[int] = set()

        for tech in tech_list:
            for contract in contract_list:
                score = self.compute_confidence(tech, contract)
                best_tech[id(tech)] = max(best_tech[id(tech)], score)
                best_contract[id(contract)] = max(best_contract[id(contract)], score)
                if score >= self.min_link_score:
                    result.links.append((self.reconcile_pair(tech, contract), tech, contract))
                    linked.update((id(tech), id(contract)))

        for tech in tech_list:
            if id(tech) not in linked:
                result.orphans.append(self._tech_orphan(tech, best_tech[id(tech)]))
        for contract in contract_list:
            if id(contract) not in linked:
                result.orphans.append(self._contract_orphan(contract, best_contract[id(contract)]))

        return result

    def score_catalog_tech(self, app: AplicacionCatalogo, tech: EvidenciaTecnica) -> float:
        """
        Score heurístico de vínculo entre una aplicación del catálogo y un repositorio.
        Fórmula: 75% similitud nominal (nombre o alias) + 25% congruencia de stack.
        El stack solo no basta para superar el score mínimo: dos sistemas Java no
        son la misma aplicación.
        """
        name_sim = max(self.calculate_name_similarity(tech.repo_name, n) for n in self._catalog_names(app))
        stack_sim = self._stack_similarity(app, tech)
        return round((0.75 * name_sim) + (0.25 * stack_sim), 3)

    def score_catalog_contract(self, app: AplicacionCatalogo, contract: EvidenciaContractual) -> float:
        """
        Score heurístico de vínculo directo entre una aplicación del catálogo y un contrato.
        Fórmula: 75% similitud nominal (nombre o alias vs. objeto del contrato) + 25% proveedor.
        """
        name_sim = max(self.calculate_name_similarity(n, contract.doc_name) for n in self._catalog_names(app))
        provider_sim = self._containment(app.provider, contract.provider_name)
        return round((0.75 * name_sim) + (0.25 * provider_sim), 3)

    def reconcile_with_catalog(
        self,
        catalog: List[AplicacionCatalogo],
        tech_list: List[EvidenciaTecnica],
        contract_list: List[EvidenciaContractual],
    ) -> ResultadoReconciliacion:
        """
        Ancla la evidencia en el catálogo existente (identidad de la aplicación).

        1. Cada repositorio se vincula a toda aplicación del catálogo con score ≥ mínimo (N:M).
        2. Cada contrato se vincula a una aplicación de forma directa (nombre/alias/proveedor)
           o a través de un repositorio ya vinculado a ella; el score transitivo es el
           menor de los dos vínculos.
        3. Hipótesis = aplicación del catálogo + repositorios + contratos vinculados.
           Su score es el del vínculo más débil.
        4. La evidencia que no coincide con ninguna aplicación es un candidato huérfano;
           los huérfanos que se vinculan entre sí se reportan como relacionados.
        """
        result = ResultadoReconciliacion()
        anchored_techs: Set[int] = set()
        anchored_contracts: Set[int] = set()
        best_tech: Dict[int, float] = {id(t): 0.0 for t in tech_list}
        best_contract: Dict[int, float] = {id(c): 0.0 for c in contract_list}

        for app in catalog:
            tech_links: List[Tuple[EvidenciaTecnica, float]] = []
            for tech in tech_list:
                score = self.score_catalog_tech(app, tech)
                best_tech[id(tech)] = max(best_tech[id(tech)], score)
                if score >= self.min_link_score:
                    tech_links.append((tech, score))

            contract_links: List[Tuple[EvidenciaContractual, float]] = []
            for contract in contract_list:
                score = self.score_catalog_contract(app, contract)
                for tech, tech_score in tech_links:
                    score = max(score, min(tech_score, self.compute_confidence(tech, contract)))
                best_contract[id(contract)] = max(best_contract[id(contract)], score)
                if score >= self.min_link_score:
                    contract_links.append((contract, score))

            if not tech_links and not contract_links:
                result.catalog_without_evidence.append(app.code)
                continue

            anchored_techs.update(id(t) for t, _ in tech_links)
            anchored_contracts.update(id(c) for c, _ in contract_links)
            result.hypotheses.append(self._anchored_hypothesis(app, tech_links, contract_links))

        orphan_techs = [t for t in tech_list if id(t) not in anchored_techs]
        orphan_contracts = [c for c in contract_list if id(c) not in anchored_contracts]
        related: Dict[str, List[str]] = {}
        for _, tech, contract in self.match_all(orphan_techs, orphan_contracts).links:
            related.setdefault(tech.repo_name, []).append(contract.doc_id)
            related.setdefault(contract.doc_id, []).append(tech.repo_name)

        reason = "Sin coincidencia con ninguna aplicación del catálogo (posible Shadow IT)."
        for tech in orphan_techs:
            orphan = self._tech_orphan(tech, best_tech[id(tech)], reason)
            orphan.related = related.get(tech.repo_name, [])
            result.orphans.append(orphan)
        for contract in orphan_contracts:
            orphan = self._contract_orphan(contract, best_contract[id(contract)], reason)
            orphan.related = related.get(contract.doc_id, [])
            result.orphans.append(orphan)

        return result

    def _anchored_hypothesis(
        self,
        app: AplicacionCatalogo,
        tech_links: List[Tuple[EvidenciaTecnica, float]],
        contract_links: List[Tuple[EvidenciaContractual, float]],
    ) -> HipotesisAnclada:
        """Construye la hipótesis de una aplicación del catálogo con su evidencia vinculada."""
        scores = [s for _, s in tech_links] + [s for _, s in contract_links]
        score = round(min(scores), 3)
        techs = [t for t, _ in sorted(tech_links, key=lambda x: -x[1])]
        contracts = [c for c, _ in sorted(contract_links, key=lambda x: -x[1])]

        if techs:
            stack = f"{techs[0].primary_language} ({techs[0].runtime_version})"
        else:
            stack = f"{app.primary_language} ({app.runtime_version})"
        provider = contracts[0].provider_name if contracts else app.provider
        sla = contracts[0].sla_uptime if contracts else app.sla_uptime

        citations: List[Dict[str, str]] = [{
            "source": "existing_catalog",
            "catalog_id": app.code,
            "attribute": "identity",
            "citation": app.citation,
        }]
        for tech in techs:
            citations.extend(self._tech_citations(tech))
        for contract in contracts:
            citations.extend(self._contract_citations(contract))

        # El responsable registrado en el catálogo prevalece; el inferido de commits es sugerencia
        technical_owner = app.technical_owner or (techs[0].top_contributor if techs else None)
        owner_suggested = not app.technical_owner and technical_owner is not None

        fact_sheet = HipotesisFactSheet(
            entity_name=app.name,
            candidate_type="Application",
            technical_stack=stack,
            provider=provider,
            sla_uptime=sla,
            confidence_score=score,
            status="Draft" if score >= self.review_threshold else "Requires_Verification",
            primary_citations=citations,
            business_owner=None,  # Requiere Micro-nudge
            technical_owner=technical_owner,
            technical_owner_suggested=owner_suggested,
            description=(
                f"Aplicación del catálogo '{app.code}' con evidencia vinculada: "
                f"repositorios {[t.repo_name for t in techs]}, contratos {[c.doc_id for c in contracts]}."
            ),
            catalog_id=app.code,
            linked_repos=[t.repo_name for t in techs],
            linked_contracts=[c.doc_id for c in contracts],
        )
        return HipotesisAnclada(fact_sheet, techs, contracts)

    def _catalog_names(self, app: AplicacionCatalogo) -> List[str]:
        """Nombre oficial y alias de una aplicación del catálogo."""
        return [app.name] + list(app.aliases)

    def _stack_similarity(self, app: AplicacionCatalogo, tech: EvidenciaTecnica) -> float:
        """Congruencia entre el stack registrado en el catálogo y el detectado en el código."""
        if not app.primary_language:
            return 0.5
        language = app.primary_language.lower()
        detected = tech.primary_language.lower()
        language_sim = 1.0 if language in detected or detected in language else 0.0
        app_version = re.search(r"\d+", app.runtime_version or "")
        tech_version = re.search(r"\d+", tech.runtime_version or "")
        version_sim = 1.0 if app_version and tech_version and app_version.group() == tech_version.group() else 0.0
        return (0.5 * language_sim) + (0.5 * version_sim)

    def _containment(self, reference: str, text: str) -> float:
        """Proporción de tokens significativos de `reference` presentes en `text`."""
        ref_tokens = self._tokenize(reference or "")
        if not ref_tokens:
            return 0.0
        return len(ref_tokens & self._tokenize(text or "")) / len(ref_tokens)

    def _tech_orphan(self, tech: EvidenciaTecnica, best_score: float, reason: Optional[str] = None) -> CandidatoHuerfano:
        """Construye un candidato huérfano a partir de un repositorio sin vínculos."""
        return CandidatoHuerfano(
            evidence_type="repositorio",
            name=tech.repo_name,
            best_score=round(best_score, 3),
            reason=reason or f"Ningún vínculo alcanza el score mínimo {self.min_link_score:.2f}.",
            primary_citations=self._tech_citations(tech),
        )

    def _contract_orphan(
        self, contract: EvidenciaContractual, best_score: float, reason: Optional[str] = None
    ) -> CandidatoHuerfano:
        """Construye un candidato huérfano a partir de un contrato sin vínculos."""
        return CandidatoHuerfano(
            evidence_type="contrato",
            name=contract.doc_id,
            best_score=round(best_score, 3),
            reason=reason or f"Ningún vínculo alcanza el score mínimo {self.min_link_score:.2f}.",
            primary_citations=self._contract_citations(contract),
        )

    def _tech_citations(self, tech: EvidenciaTecnica) -> List[Dict[str, str]]:
        """Citas primarias de una evidencia técnica (Principio OCDE 1.3)."""
        return [
            {
                "source": "repository_code",
                "entity": tech.repo_name,
                "commit": tech.commit_hash,
                "attribute": key,
                "citation": ref,
            }
            for key, ref in tech.file_citations.items()
        ]

    def _contract_citations(self, contract: EvidenciaContractual) -> List[Dict[str, str]]:
        """Citas primarias de una evidencia contractual (Principio OCDE 1.3)."""
        return [
            {
                "source": "contract_dark_data",
                "doc_id": contract.doc_id,
                "attribute": key,
                "citation": ref,
            }
            for key, ref in contract.doc_citations.items()
        ]

    def _tokenize(self, text: str) -> Set[str]:
        """Limpia y tokeniza un texto eliminando tildes y stopwords."""
        normalized = "".join(
            c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
        )
        clean = re.sub(r"[^a-zA-Z0-9\s]", " ", normalized.lower())
        tokens = [t.strip() for t in clean.split() if len(t.strip()) > 2]
        return {t for t in tokens if t not in self.STOPWORDS}


_CATALOG_COLUMNS: List[Tuple[str, Tuple[str, ...]]] = [
    ("code", ("codigo", "code")),
    ("aliases", ("alias",)),
    ("name", ("nombre", "aplicacion", "sistema")),
    ("technical_owner", ("responsable", "propietario", "owner")),
    ("primary_language", ("lenguaje", "tecnologia", "stack")),
    ("runtime_version", ("runtime", "version")),
    ("dependencies", ("dependencia", "libreria")),
    ("sla_uptime", ("sla", "uptime", "disponibilidad")),
    ("provider", ("proveedor", "vendor", "contratista")),
]


def load_catalog(path: Union[str, Path]) -> List[AplicacionCatalogo]:
    """
    Carga el catálogo existente de aplicaciones (.csv o .xlsx) como ancla de identidad.
    Reutiliza los lectores del SpreadsheetConnector; el alias admite varios valores
    separados por '|'.
    """
    p = Path(path)
    connector = SpreadsheetConnector()
    rows = connector._read_csv(p) if p.suffix.lower() == ".csv" else connector._read_xlsx(p)[0]
    if not rows:
        return []

    mapping: Dict[str, int] = {}
    for idx, header in enumerate(rows[0]):
        norm = _normalize_text(header)
        for attr, keywords in _CATALOG_COLUMNS:
            matches = any(k in norm for k in keywords) or (attr == "code" and norm == "id")
            if matches and attr not in mapping:
                mapping[attr] = idx
                break

    def cell(row: List[str], attr: str) -> str:
        idx = mapping.get(attr)
        return row[idx].strip() if idx is not None and idx < len(row) else ""

    catalog: List[AplicacionCatalogo] = []
    for offset, row in enumerate(rows[1:]):
        name = cell(row, "name")
        if not name:
            continue
        row_num = offset + 2
        catalog.append(AplicacionCatalogo(
            code=cell(row, "code") or f"{p.stem}-R{row_num}",
            name=name,
            aliases=[a.strip() for a in cell(row, "aliases").split("|") if a.strip()],
            technical_owner=cell(row, "technical_owner"),
            primary_language=cell(row, "primary_language"),
            runtime_version=cell(row, "runtime_version"),
            dependencies=[d.strip() for d in re.split(r"[,;|]", cell(row, "dependencies")) if d.strip()],
            sla_uptime=cell(row, "sla_uptime"),
            provider=cell(row, "provider"),
            citation=f"{p.name}#R{row_num}",
        ))
    return catalog
