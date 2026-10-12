"""
Conector federado para presentaciones ejecutivas y de arquitectura (.pptx).

Extrae texto arquitectónico, nombres de sistemas, especificaciones técnicas y
notas de orador a partir de archivos OpenXML PowerPoint (.pptx), generando
EvidenciaTecnica y EvidenciaDiagrama con citas canónicas a nivel de diapositiva
y forma (ej. presentacion.pptx#Slide3!Shape4).
Implementado completamente en la biblioteca estándar de Python (zipfile + ElementTree).
"""

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..models import EvidenciaDiagrama, EvidenciaTecnica
from .base import BaseConnector

# Expresiones regulares para detección de componentes de software en diapositivas
SYSTEM_PATTERNS = [
    re.compile(r"(?:Sistema|Plataforma|Portal|Servicio|Módulo|Modulo|Microservicio|API|Motor|Gateway|Aplicación|Aplicacion)\s+([A-Za-zÁÉÍÓÚáéíóúñ0-9_\-\s]{3,40})", re.IGNORECASE),
    re.compile(r"([A-Za-zÁÉÍÓÚáéíóúñ0-9_\-]+\s*(?:Service|Portal|API|Engine|Gateway|Backend|Frontend))", re.IGNORECASE),
]

TECH_KEYWORDS = [
    "Java", "Python", "Node.js", "TypeScript", "JavaScript", "Docker", "Kubernetes",
    "PostgreSQL", "Oracle", "MySQL", "MongoDB", "Redis", "Kafka", "Spring Boot",
    "FastAPI", "React", "Angular", "Vue", "AWS", "Azure", "GCP", "Linux", "REST",
    "GraphQL", "Microservicios", "OpenAPI", "Swagger"
]


class PresentationConnector(BaseConnector):
    """
    Conector para procesar presentaciones de arquitectura en formato .pptx.
    """

    name: str = "PresentationConnector"
    supported_extensions: List[str] = [".pptx"]

    def can_handle(self, path: Union[str, Path]) -> bool:
        p = Path(path)
        if p.is_dir():
            return False
        return p.suffix.lower() in [ext.lower() for ext in self.supported_extensions]

    def extract(self, path: Union[str, Path]) -> List[Any]:
        """
        Extrae evidencias técnicas y arquitectónicas desde un archivo .pptx.
        
        Returns:
            Lista con EvidenciaTecnica (por cada sistema/aplicación identificada)
            y EvidenciaDiagrama (resumen arquitectónico de diapositivas con componentes).
        """
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")

        slides_data = self._read_pptx(p)
        if not slides_data:
            return []

        evidences: List[Any] = []
        all_components: Set[str] = set()
        diagram_citations: Dict[str, str] = {}
        diagram_relations: List[Dict[str, str]] = []

        for slide_idx, shapes, notes in slides_data:
            slide_title = ""
            slide_text_blocks: List[str] = []
            slide_citations: Dict[str, str] = {}
            slide_systems: Set[str] = set()
            slide_techs: Set[str] = set()

            for shape_id, shape_name, text in shapes:
                clean_text = text.strip()
                if not clean_text:
                    continue

                slide_text_blocks.append(clean_text)
                citation_key = f"{p.name}#Slide{slide_idx}!Shape{shape_id}"
                slide_citations[citation_key] = clean_text[:120]

                # Si es un título o forma de cabecera
                if ("title" in shape_name.lower() or shape_id in ["2", "1"]) and not slide_title:
                    slide_title = clean_text.split("\n")[0]

                # Buscar nombres de sistemas en el texto de la forma
                for pat in SYSTEM_PATTERNS:
                    for match in pat.finditer(clean_text):
                        found_name = match.group(0).strip()
                        # Evitar falsos positivos excesivamente largos
                        if 4 <= len(found_name) <= 50 and not found_name.endswith("."):
                            slide_systems.add(found_name)
                            all_components.add(found_name)

                # Buscar tecnologías
                for kw in TECH_KEYWORDS:
                    if re.search(r"\b" + re.escape(kw) + r"\b", clean_text, re.IGNORECASE):
                        slide_techs.add(kw)

            # Buscar posibles emails de contacto o autores
            slide_full_text = " ".join(slide_text_blocks)
            owner = self._extract_owner(slide_full_text, notes)

            # Para cada sistema detectado en la diapositiva, generar EvidenciaTecnica
            for sys_name in slide_systems:
                primary_lang = self._infer_primary_language(list(slide_techs))
                ev = EvidenciaTecnica(
                    repo_name=sys_name,
                    commit_hash=f"pptx-slide-{slide_idx}",
                    primary_language=primary_lang,
                    runtime_version="N/A",
                    dependencies=sorted(list(slide_techs)),
                    endpoints=[],
                    top_contributor=owner,
                    file_citations=dict(slide_citations),
                )
                evidences.append(ev)

            # Si la diapositiva tiene múltiples sistemas o componentes, registrar relaciones implícitas
            sys_list = list(slide_systems)
            if len(sys_list) >= 2:
                for i in range(len(sys_list) - 1):
                    diagram_relations.append({
                        "source": sys_list[i],
                        "target": sys_list[i + 1],
                        "relation_type": f"Slide {slide_idx}: Arquitectura compartida",
                    })

            diagram_citations.update(slide_citations)

        # Generar EvidenciaDiagrama si se encontraron componentes en la presentación
        if all_components:
            diag_ev = EvidenciaDiagrama(
                source_file=p.name,
                format_type="PowerPoint (PPTX)",
                components=sorted(list(all_components)),
                relations=diagram_relations,
                citations=diagram_citations,
            )
            evidences.append(diag_ev)

        return evidences

    def _read_pptx(self, path: Path) -> List[Tuple[int, List[Tuple[str, str, str]], str]]:
        """
        Lee el archivo .pptx y extrae (slide_index, [(shape_id, shape_name, text)], notes_text).
        """
        results: List[Tuple[int, List[Tuple[str, str, str]], str]] = []

        with zipfile.ZipFile(path, "r") as zf:
            namelist = zf.namelist()
            # Identificar diapositivas ordenadas numéricamente
            slide_files = [f for f in namelist if f.startswith("ppt/slides/slide") and f.endswith(".xml")]

            def extract_slide_num(s: str) -> int:
                m = re.search(r"slide(\d+)\.xml", s)
                return int(m.group(1)) if m else 9999

            slide_files.sort(key=extract_slide_num)

            for sfile in slide_files:
                slide_num = extract_slide_num(sfile)
                shapes_info: List[Tuple[str, str, str]] = []

                try:
                    tree = ET.fromstring(zf.read(sfile))
                    # Recorrer formas (p:sp)
                    for sp in tree.iter():
                        if not sp.tag.endswith("sp"):
                            continue

                        # Obtener id y nombre de forma
                        shape_id = "0"
                        shape_name = "Shape"
                        for child in sp.iter():
                            if child.tag.endswith("cNvPr"):
                                shape_id = child.attrib.get("id", "0")
                                shape_name = child.attrib.get("name", "Shape")
                                break

                        # Extraer textos (<a:t>)
                        text_fragments: List[str] = []
                        for t_elem in sp.iter():
                            if t_elem.tag.endswith("t") and t_elem.text:
                                text_fragments.append(t_elem.text)

                        full_text = " ".join(text_fragments).strip()
                        if full_text:
                            shapes_info.append((shape_id, shape_name, full_text))

                except Exception:
                    continue

                # Intentar leer notas de orador asociadas si existen
                notes_text = ""
                notes_file = f"ppt/notesSlides/notesSlide{slide_num}.xml"
                if notes_file in namelist:
                    try:
                        ntree = ET.fromstring(zf.read(notes_file))
                        ntexts = [e.text for e in ntree.iter() if e.tag.endswith("t") and e.text]
                        notes_text = " ".join(ntexts).strip()
                    except Exception:
                        pass

                results.append((slide_num, shapes_info, notes_text))

        return results

    def _extract_owner(self, text: str, notes: str) -> str:
        combined = f"{text} {notes}"
        email_match = re.search(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", combined)
        if email_match:
            return email_match.group(1)
        for lead in ["Arquitectura", "Dirección TI", "Equipo Core", "Equipo de Desarrollo"]:
            if lead.lower() in combined.lower():
                return f"{lead} <arquitectura@mef.gob.pe>"
        return "Desconocido"

    def _infer_primary_language(self, techs: List[str]) -> str:
        tech_set = {t.lower() for t in techs}
        if "java" in tech_set or "spring boot" in tech_set:
            return "Java"
        if "typescript" in tech_set or "angular" in tech_set or "react" in tech_set:
            return "TypeScript"
        if "python" in tech_set or "fastapi" in tech_set:
            return "Python"
        if "javascript" in tech_set or "node.js" in tech_set:
            return "JavaScript / TypeScript"
        return techs[0] if techs else "Desconocido"
