"""
Minero de Dark Data y Contratos (Contract Miner).

Este módulo implementa el Agente 2 del pipeline de descubrimiento continuo:
procesa documentos semiestructurados y no estructurados (TDRs, contratos, adendas)
en formatos Markdown o texto plano, extrayendo metadatos contractuales críticos
(proveedor, vigencias, SLAs de uptime, licenciamiento) y manteniendo citas
primarias a nivel de cláusula/página (Principio OCDE 1.3).
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import EvidenciaContractual


class ContractMiner:
    """
    Agente que procesa Dark Data contractual para extraer atributos formales
    de gobierno de aplicaciones y acuerdos de servicio.
    """

    def __init__(self):
        # Patrones de expresión regular estructurados
        self.doc_id_pattern = re.compile(
            r"(?:código|id|referencia|número|contrato|tdr).*?[:\s]+([A-Z0-9]{2,8}-\d{4}-[A-Z0-9\-]+)",
            re.IGNORECASE,
        )
        self.provider_pattern = re.compile(
            r"(?:proveedor(?:\s+adjudicado)?|contratista|adjudicatario|empresa)[\s:]+([^\n\r]+)",
            re.IGNORECASE,
        )
        self.sla_pattern = re.compile(
            r"(?:sla|disponibilidad|uptime).*?(\d{2}(?:\.\d{1,3})?)\s*%",
            re.IGNORECASE,
        )
        self.date_range_pattern = re.compile(
            r"(?:vigencia|periodo|plazo)[\s:\w]*?(?:desde|del)?\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})\s*(?:hasta|al)\s*(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})",
            re.IGNORECASE,
        )
        self.start_date_pattern = re.compile(
            r"(?:fecha\s+de\s+inicio|inicio\s+de\s+vigencia)[\s:]+(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})",
            re.IGNORECASE,
        )
        self.end_date_pattern = re.compile(
            r"(?:fecha\s+de\s+culminación|fecha\s+de\s+fin|fin\s+de\s+vigencia)[\s:]+(\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})",
            re.IGNORECASE,
        )
        self.clause_header_pattern = re.compile(
            r"^(?:#{1,4}\s+|[0-9]+\.\s+)?(Cláusula\s+[0-9\.]+|Artículo\s+[0-9\.]+|Sección\s+[0-9\.]+|[0-9]+\.\s+[A-Za-zÁÉÍÓÚáéíóúñ\s]+)",
            re.IGNORECASE,
        )

    def extract(self, doc_path: str) -> EvidenciaContractual:
        """
        Lee y procesa un documento contractual o TDR.
        """
        path = Path(doc_path)
        if not path.is_file():
            raise FileNotFoundError(f"El archivo contractual no existe: {doc_path}")

        filename = path.name
        doc_name = ""
        doc_id = ""
        provider_name = ""
        sla_uptime = "N/A"
        contract_dates: Dict[str, str] = {}
        acquired_licenses: List[str] = []
        doc_citations: Dict[str, str] = {}

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        current_clause = "Encabezado General"

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped:
                continue

            # Detectar título del documento (primer encabezado Markdown)
            if not doc_name and stripped.startswith("# "):
                doc_name = stripped.lstrip("# ").strip()
                doc_citations["doc_title"] = f"{filename}#L{idx}"

            # Detectar cambio de cláusula o sección
            clause_match = self.clause_header_pattern.search(stripped)
            if clause_match:
                current_clause = clause_match.group(1).strip()

            is_header = stripped.startswith("#")

            # 1. Extracción de Identificador de Documento
            if not doc_id and not is_header:
                m_id = self.doc_id_pattern.search(stripped)
                if m_id:
                    doc_id = m_id.group(1).strip()
                    doc_citations["doc_id"] = f"{filename}#{current_clause} (L{idx})"

            # 2. Extracción de Proveedor
            if not provider_name and not is_header:
                m_prov = self.provider_pattern.search(stripped)
                if m_prov:
                    provider_raw = m_prov.group(1).strip()
                    # Limpiar caracteres sobrantes
                    provider_name = re.sub(r"^[:\s\-]+", "", re.sub(r"[\*\_\:\(\)]", "", provider_raw)).strip()
                    doc_citations["provider"] = f"{filename}#{current_clause} (L{idx})"

            # 3. Extracción de SLA de Uptime
            if sla_uptime == "N/A":
                m_sla = self.sla_pattern.search(stripped)
                if m_sla:
                    sla_uptime = f"{m_sla.group(1).strip()}%"
                    doc_citations["sla_uptime"] = f"{filename}#{current_clause} (L{idx})"

            # 4. Extracción de Fechas de Vigencia
            m_range = self.date_range_pattern.search(stripped)
            if m_range:
                contract_dates["start_date"] = m_range.group(1).strip()
                contract_dates["end_date"] = m_range.group(2).strip()
                doc_citations["contract_dates"] = f"{filename}#{current_clause} (L{idx})"
            else:
                m_start = self.start_date_pattern.search(stripped)
                if m_start and "start_date" not in contract_dates:
                    contract_dates["start_date"] = m_start.group(1).strip()
                    doc_citations["start_date"] = f"{filename}#{current_clause} (L{idx})"

                m_end = self.end_date_pattern.search(stripped)
                if m_end and "end_date" not in contract_dates:
                    contract_dates["end_date"] = m_end.group(1).strip()
                    doc_citations["end_date"] = f"{filename}#{current_clause} (L{idx})"

            # 5. Extracción de Licenciamiento / Tecnologías contratadas
            if re.search(r"(?:licencia|licenciamiento|stack|software|tecnolog[ií]a)", stripped, re.IGNORECASE):
                # Detectar tecnologías conocidas
                known_techs = [
                    "PostgreSQL", "Oracle", "MySQL", "SQL Server",
                    "Java", "OpenJDK", "Spring Boot", "Spring",
                    "Node.js", "React", "Next.js", "Angular", "Vue",
                    "Python", "Django", "FastAPI", "Go", "Docker", "Kubernetes",
                    "Red Hat Enterprise Linux", "Debian", "Ubuntu", "Alpine"
                ]
                for tech in known_techs:
                    if re.search(rf"\b{re.escape(tech)}\b", stripped, re.IGNORECASE):
                        if tech not in acquired_licenses:
                            acquired_licenses.append(tech)
                            doc_citations[f"license_{tech}"] = f"{filename}#{current_clause} (L{idx})"

        # Fallbacks limpios
        if not doc_name:
            doc_name = filename.replace(".md", "").replace(".txt", "").replace("-", " ").title()

        if not doc_id:
            # Buscar en el nombre de archivo o generar hash determinista
            m_fn = re.search(r"([A-Z]{3,5}-\d{4}-[A-Z0-9\-]+)", filename, re.IGNORECASE)
            doc_id = m_fn.group(1).upper() if m_fn else f"DOC-{filename[:8].upper()}"

        if not provider_name:
            provider_name = "Proveedor no especificado"

        return EvidenciaContractual(
            doc_name=doc_name,
            doc_id=doc_id,
            provider_name=provider_name,
            contract_dates=contract_dates,
            sla_uptime=sla_uptime,
            acquired_licenses=acquired_licenses,
            doc_citations=doc_citations,
        )
