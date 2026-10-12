"""
Generador de Micro-Nudges (Micro-Nudge Generator).

Este módulo implementa el Agente 4 del pipeline de descubrimiento continuo:
evalúa si las hipótesis reconciliadas tienen un score heurístico inferior al
umbral único de revisión (`config.REVIEW_THRESHOLD`, compartido con el
reconciliador), presentan atributos críticos vacíos (ej. Dueño de Negocio) o
un dueño técnico solo sugerido a partir de los commits.
Genera micro-solicitudes interactivas en formato Adaptive Card de Teams/Slack
con botones de confirmación en 1 clic (Principio OCDE 1.2: Supervisión Humana).
"""

from typing import Any, Dict, List, Optional

from . import config
from .models import EvidenciaContractual, EvidenciaTecnica, HipotesisFactSheet, MicroNudge


class NudgeGenerator:
    """
    Agente que genera micro-solicitudes no intrusivas hacia los responsables
    técnicos para enriquecer progresivamente el catálogo APM sin fricción operativa.
    """

    def __init__(self, review_threshold: float = config.REVIEW_THRESHOLD):
        self.review_threshold = review_threshold

    def evaluate_and_generate(
        self,
        hipotesis: HipotesisFactSheet,
        tech: Optional[EvidenciaTecnica] = None,
        contract: Optional[EvidenciaContractual] = None,
    ) -> List[MicroNudge]:
        """
        Inspecciona una HipotesisFactSheet y genera los MicroNudges correspondientes
        si el score es inferior al umbral de revisión, faltan campos obligatorios
        o el dueño técnico es solo una sugerencia.
        """
        nudges: List[MicroNudge] = []
        recipient = (tech.top_contributor if tech else hipotesis.technical_owner) or "arquitectura@mef.gob.pe"
        channel = "Microsoft Teams / Slack"

        # 1. Caso A: Score inferior al umbral único de revisión
        if hipotesis.confidence_score < self.review_threshold:
            nudge_conf = self._create_confidence_nudge(hipotesis, recipient, channel, tech, contract)
            nudges.append(nudge_conf)

        # 2. Caso B: Falta Dueño de Negocio (Business Owner)
        if not hipotesis.business_owner:
            nudge_bo = self._create_business_owner_nudge(hipotesis, recipient, channel)
            nudges.append(nudge_bo)

        # 3. Caso C: Dueño técnico inferido de commits: sugerencia que siempre se confirma
        if hipotesis.technical_owner and hipotesis.technical_owner_suggested:
            nudge_to = self._create_tech_owner_nudge(hipotesis, recipient, channel, tech)
            nudges.append(nudge_to)

        return nudges

    def _create_confidence_nudge(
        self,
        hipotesis: HipotesisFactSheet,
        recipient: str,
        channel: str,
        tech: Optional[EvidenciaTecnica],
        contract: Optional[EvidenciaContractual],
    ) -> MicroNudge:
        """Crea un micro-nudge cuando el score heurístico requiere confirmación humana."""
        repo_name = tech.repo_name if tech else "repositorio escaneado"
        contract_id = contract.doc_id if contract else "contrato"
        score_txt = f"{hipotesis.confidence_score:.2f}"

        title = f"Validación de Correlación: {hipotesis.entity_name}"
        summary = (
            f"El motor de descubrimiento correlacionó el código de '{repo_name}' con el "
            f"documento '{contract_id}' con un score heurístico de {score_txt} "
            f"(umbral de revisión: {self.review_threshold:.2f}). "
            f"Se requiere tu confirmación para consolidar este Fact Sheet en el catálogo APM."
        )
        proposed_value = f"Vincular '{repo_name}' con '{hipotesis.entity_name}'"

        quick_actions = [
            {"id": "confirm_correlation", "label": "✅ Confirmar Asociación (1 clic)", "action": "approve_correlation"},
            {"id": "reject_correlation", "label": "❌ Rechazar y Desvincular", "action": "reject_correlation"},
        ]

        payload = self._build_adaptive_card(
            title=title,
            body_text=summary,
            facts=[
                {"title": "Entidad APM:", "value": hipotesis.entity_name},
                {"title": "Repositorio:", "value": repo_name},
                {"title": "Contrato/TDR:", "value": contract_id},
                {"title": "Score heurístico:", "value": score_txt},
                {"title": "Stack Detectado:", "value": hipotesis.technical_stack},
            ],
            actions=[
                {
                    "type": "Action.Submit",
                    "title": "✅ Confirmar (1 clic)",
                    "data": {
                        "action": "approve_correlation",
                        "entity": hipotesis.entity_name,
                        "repo": repo_name,
                    },
                },
                {
                    "type": "Action.Submit",
                    "title": "❌ Desvincular",
                    "data": {
                        "action": "reject_correlation",
                        "entity": hipotesis.entity_name,
                    },
                },
            ],
        )

        return MicroNudge(
            recipient=recipient,
            channel=channel,
            question_title=title,
            context_summary=summary,
            proposed_value=proposed_value,
            quick_actions=quick_actions,
            payload=payload,
        )

    def _create_business_owner_nudge(
        self,
        hipotesis: HipotesisFactSheet,
        recipient: str,
        channel: str,
    ) -> MicroNudge:
        """Crea un micro-nudge para asignar el Dueño de Negocio."""
        title = f"Asignación de Dueño de Negocio: {hipotesis.entity_name}"
        summary = (
            f"El Fact Sheet '{hipotesis.entity_name}' tiene stack técnico y proveedor "
            f"identificados, pero no cuenta con un Dueño de Negocio (Business Owner) asignado."
        )
        proposed_value = "Dirección General de Tesoro Público (Sugerido)"

        quick_actions = [
            {"id": "confirm_default_bo", "label": "Confirmar Tesoro Público", "action": "set_bo_tesoro"},
            {"id": "custom_bo", "label": "Especificar otra área", "action": "prompt_bo"},
        ]

        payload = self._build_adaptive_card(
            title=title,
            body_text=summary,
            facts=[
                {"title": "Aplicación:", "value": hipotesis.entity_name},
                {"title": "Proveedor:", "value": hipotesis.provider},
                {"title": "SLA Uptime:", "value": hipotesis.sla_uptime},
            ],
            actions=[
                {
                    "type": "Action.Submit",
                    "title": "Aceptar Sugerido",
                    "data": {
                        "action": "set_business_owner",
                        "entity": hipotesis.entity_name,
                        "owner": proposed_value,
                    },
                },
                {
                    "type": "Action.ShowCard",
                    "title": "Indicar otro responsable",
                    "card": {
                        "type": "AdaptiveCard",
                        "body": [
                            {
                                "type": "Input.Text",
                                "id": "custom_business_owner",
                                "placeholder": "Correo o nombre del líder de negocio",
                            }
                        ],
                        "actions": [
                            {"type": "Action.Submit", "title": "Guardar", "data": {"action": "submit_custom_bo"}}
                        ],
                    },
                },
            ],
        )

        return MicroNudge(
            recipient=recipient,
            channel=channel,
            question_title=title,
            context_summary=summary,
            proposed_value=proposed_value,
            quick_actions=quick_actions,
            payload=payload,
        )

    def _create_tech_owner_nudge(
        self,
        hipotesis: HipotesisFactSheet,
        recipient: str,
        channel: str,
        tech: Optional[EvidenciaTecnica],
    ) -> MicroNudge:
        """Crea un micro-nudge para confirmar el Dueño Técnico sugerido a partir de los commits."""
        repo_name = tech.repo_name if tech else "el repositorio"
        suggested_owner = hipotesis.technical_owner or recipient
        title = f"Confirmación de Dueño Técnico (sugerido): {hipotesis.entity_name}"
        summary = (
            f"Hola {suggested_owner}. Según el historial de commits de '{repo_name}', eres el "
            f"principal contribuyente técnico. Esto es solo una sugerencia: ¿confirmas tu "
            f"designación como Dueño Técnico en APM o indicas a otra persona?"
        )
        proposed_value = f"{suggested_owner} (sugerido)"

        quick_actions = [
            {"id": "confirm_tech_owner", "label": "✅ Sí, soy Dueño Técnico", "action": "confirm_to"},
            {"id": "reassign_tech_owner", "label": "🔄 Indicar otro colega", "action": "reassign_to"},
        ]

        payload = self._build_adaptive_card(
            title=title,
            body_text=summary,
            facts=[
                {"title": "Aplicación:", "value": hipotesis.entity_name},
                {"title": "Repositorio:", "value": repo_name},
                {"title": "Rol propuesto:", "value": "Technical Owner / Architect (sugerido)"},
            ],
            actions=[
                {
                    "type": "Action.Submit",
                    "title": "✅ Confirmar en 1 clic",
                    "data": {
                        "action": "confirm_tech_owner",
                        "entity": hipotesis.entity_name,
                        "owner": suggested_owner,
                    },
                },
                {
                    "type": "Action.Submit",
                    "title": "🔄 Reasignar a colega",
                    "data": {
                        "action": "reassign_tech_owner",
                        "entity": hipotesis.entity_name,
                    },
                },
            ],
        )

        return MicroNudge(
            recipient=recipient,
            channel=channel,
            question_title=title,
            context_summary=summary,
            proposed_value=proposed_value,
            quick_actions=quick_actions,
            payload=payload,
        )

    def _build_adaptive_card(
        self,
        title: str,
        body_text: str,
        facts: List[Dict[str, str]],
        actions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Construye un payload JSON conforme a la especificación Microsoft Adaptive Card v1.4."""
        card: Dict[str, Any] = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "🛡️ APM - Descubrimiento Continuo IA",
                    "size": "Medium",
                    "weight": "Bolder",
                    "color": "Accent",
                },
                {
                    "type": "TextBlock",
                    "text": title,
                    "weight": "Bolder",
                    "size": "Default",
                    "wrap": True,
                },
                {
                    "type": "TextBlock",
                    "text": body_text,
                    "wrap": True,
                },
                {
                    "type": "FactSet",
                    "facts": facts,
                },
            ],
            "actions": actions,
        }
        return card
