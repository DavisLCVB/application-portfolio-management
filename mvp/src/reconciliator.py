"""
Reconciliador Semántico (Semantic Reconciliator).

Este módulo implementa el Agente 3 del pipeline de descubrimiento continuo:
resuelve la brecha ontológica y nominal entre los artefactos técnicos (repositorios,
código, manifiestos) y los documentos legales/contractuales (Dark Data: TDRs).
Calcula un puntaje probabilístico de confianza multivariable (0.0 a 1.0) y
sintetiza una HipotesisFactSheet compatible con LeanIX v4 y principios OCDE.
"""

import difflib
import re
import unicodedata
from typing import Dict, List, Set

from . import config
from .models import (
    CandidatoHuerfano,
    EvidenciaContractual,
    EvidenciaTecnica,
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

    def __init__(self, confidence_threshold: float = 0.85, min_link_score: float = config.MIN_LINK_SCORE):
        self.confidence_threshold = confidence_threshold
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
        Calcula el puntaje de confianza probabilístico ponderado multivariable.
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

        status = "Draft" if score >= self.confidence_threshold else "Requires_Verification"

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

    def _tech_orphan(self, tech: EvidenciaTecnica, best_score: float) -> CandidatoHuerfano:
        """Construye un candidato huérfano a partir de un repositorio sin vínculos."""
        return CandidatoHuerfano(
            evidence_type="repositorio",
            name=tech.repo_name,
            best_score=round(best_score, 3),
            reason=f"Ningún vínculo alcanza el score mínimo {self.min_link_score:.2f}.",
            primary_citations=self._tech_citations(tech),
        )

    def _contract_orphan(self, contract: EvidenciaContractual, best_score: float) -> CandidatoHuerfano:
        """Construye un candidato huérfano a partir de un contrato sin vínculos."""
        return CandidatoHuerfano(
            evidence_type="contrato",
            name=contract.doc_id,
            best_score=round(best_score, 3),
            reason=f"Ningún vínculo alcanza el score mínimo {self.min_link_score:.2f}.",
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
