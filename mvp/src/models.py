"""
Modelos de datos canónicos para el Pipeline de Descubrimiento Continuo.

Este módulo define las entidades de datos que transitan a través del pipeline
multi-agente, asegurando trazabilidad formal, citas de evidencia primaria
(Principios OCDE 1.2 y 1.3) y compatibilidad con el Meta-modelo LeanIX v4.
"""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EvidenciaTecnica:
    """
    Representa la evidencia técnica extraída directamente del código fuente,
    manifiestos de empaquetado, contenedores y control de versiones por el
    agente Code-to-Catalog.
    """
    repo_name: str
    commit_hash: str
    primary_language: str
    runtime_version: str
    dependencies: List[str] = field(default_factory=list)
    endpoints: List[str] = field(default_factory=list)
    top_contributor: str = "Desconocido"
    file_citations: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la evidencia técnica a un diccionario estándar."""
        return asdict(self)


@dataclass
class EvidenciaContractual:
    """
    Representa la evidencia contractual y documental extraída de documentos
    no estructurados (Dark Data: TDRs, contratos, adendas) por el agente
    Dark Data Miner.
    """
    doc_name: str
    doc_id: str
    provider_name: str
    contract_dates: Dict[str, str] = field(default_factory=dict)
    sla_uptime: str = "N/A"
    acquired_licenses: List[str] = field(default_factory=list)
    doc_citations: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la evidencia contractual a un diccionario estándar."""
        return asdict(self)


@dataclass
class EvidenciaDiagrama:
    """
    Representa evidencia arquitectónica extraída de diagramas y modelos
    técnicos (PlantUML, Archi XML / Open Exchange, draw.io XML) por el DiagramConnector.
    Permite descubrir componentes de aplicación, interfaces y flujos de integración.
    """
    source_file: str
    format_type: str
    components: List[str] = field(default_factory=list)
    relations: List[Dict[str, str]] = field(default_factory=list)
    citations: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la evidencia de diagrama a un diccionario estándar."""
        return asdict(self)


@dataclass
class AplicacionCatalogo:
    """
    Aplicación ya registrada en el catálogo existente (Excel migrado / CMDB).
    Es el ancla de identidad del reconciliador: la evidencia nueva se adjunta
    a estas entradas en lugar de construir entidades desde cero.
    """
    code: str
    name: str
    aliases: List[str] = field(default_factory=list)
    technical_owner: str = ""
    primary_language: str = ""
    runtime_version: str = ""
    dependencies: List[str] = field(default_factory=list)
    sla_uptime: str = ""
    provider: str = ""
    citation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la aplicación del catálogo a un diccionario estándar."""
        return asdict(self)


@dataclass
class HipotesisFactSheet:
    """
    Representa una hipótesis unificada de Fact Sheet candidata a ser publicada
    en el catálogo APM (LeanIX v4), generada por el Agente Reconciliador Semántico.
    Contiene un puntaje probabilístico de confianza y citas primarias completas.
    """
    entity_name: str
    candidate_type: str
    technical_stack: str
    provider: str
    sla_uptime: str
    confidence_score: float
    status: str
    primary_citations: List[Dict[str, Any]] = field(default_factory=list)
    business_owner: Optional[str] = None
    technical_owner: Optional[str] = None
    description: str = ""
    catalog_id: Optional[str] = None
    linked_repos: List[str] = field(default_factory=list)
    linked_contracts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la hipótesis de Fact Sheet a un diccionario estándar."""
        return asdict(self)


@dataclass
class CandidatoHuerfano:
    """
    Evidencia sin coincidencia por encima del score mínimo de vinculación
    (posible Shadow IT). "Sin coincidencia" es un resultado válido: el
    reconciliador nunca fuerza un vínculo; el arquitecto decide si es una
    aplicación nueva, un componente de otra o un descarte.
    """
    evidence_type: str
    name: str
    best_score: float
    reason: str
    primary_citations: List[Dict[str, Any]] = field(default_factory=list)
    related: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el candidato huérfano a un diccionario estándar."""
        return asdict(self)


@dataclass
class HipotesisAnclada:
    """
    Hipótesis anclada en el catálogo: aplicación del catálogo + repositorios
    vinculados + contratos vinculados (relación N:M).
    """
    fact_sheet: "HipotesisFactSheet"
    technical_evidences: List[EvidenciaTecnica] = field(default_factory=list)
    contractual_evidences: List[EvidenciaContractual] = field(default_factory=list)


@dataclass
class ResultadoReconciliacion:
    """
    Resultado del Agente 3: vínculos N:M (hipótesis, evidencia técnica,
    evidencia contractual), hipótesis ancladas en el catálogo, candidatos
    huérfanos y aplicaciones del catálogo sin evidencia nueva.
    """
    links: List[Tuple["HipotesisFactSheet", EvidenciaTecnica, EvidenciaContractual]] = field(default_factory=list)
    orphans: List[CandidatoHuerfano] = field(default_factory=list)
    hypotheses: List[HipotesisAnclada] = field(default_factory=list)
    catalog_without_evidence: List[str] = field(default_factory=list)


@dataclass
class MicroNudge:
    """
    Representa una micro-solicitud interactiva generada por el Agente Micro-Nudge
    para resolver ambigüedades o vacíos con mínima fricción hacia los dueños técnicos.
    Diseñado para integrarse en canales de chat (Teams/Slack) mediante Adaptive Cards.
    """
    recipient: str
    channel: str
    question_title: str
    context_summary: str
    proposed_value: str
    quick_actions: List[Dict[str, str]] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el micro-nudge a un diccionario estándar."""
        return asdict(self)
