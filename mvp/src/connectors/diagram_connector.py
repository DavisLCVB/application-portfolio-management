"""
Conector federado para diagramas y modelos de arquitectura técnica.

Soporta 3 formatos estándar de la industria:
1. PlantUML (.puml): Macro ArchiMate 3.2, C4-PlantUML y sintaxis de componentes.
2. Archi XML / Open Exchange Format (.archimate, .xml): Modelos Archi y The Open Group.
3. draw.io XML (.drawio, .xml): Esquemas gráficos mxGraphModel y mxCell.

Genera instancias canónicas de EvidenciaDiagrama con componentes, relaciones
y citas trazables a nivel de línea o identificador de celda XML.
Implementado 100% en la biblioteca estándar de Python (re, xml.etree.ElementTree, html).
"""

import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..models import EvidenciaDiagrama
from .base import BaseConnector

# Patrones para componentes en PlantUML (ArchiMate, C4, Standard)
PLANTUML_MACRO_PATTERN = re.compile(
    r"^(?:[ \t]*)([A-Za-z0-9_]+)\s*\(\s*([a-zA-Z0-9_\-]+)\s*,\s*\"([^\"]*)\"",
    re.MULTILINE,
)
PLANTUML_STD_COMPONENT = re.compile(
    r"^(?:[ \t]*)(?:component|node|artifact|class|package)\s+\"([^\"]+)\"(?:\s+as\s+([a-zA-Z0-9_\-]+))?",
    re.MULTILINE | re.IGNORECASE,
)
PLANTUML_REL_MACRO = re.compile(
    r"^(?:[ \t]*)(Rel_[A-Za-z0-9_]+)\s*\(\s*([a-zA-Z0-9_\-]+)\s*,\s*([a-zA-Z0-9_\-]+)\s*(?:,\s*\"([^\"]*)\")?",
    re.MULTILINE,
)
PLANTUML_REL_ARROW = re.compile(
    r"^(?:[ \t]*)([a-zA-Z0-9_\-]+)\s*(-{1,4}>|\.{1,4}>|<-{1,4}|<\.{1,4}|-{1,4})\s*([a-zA-Z0-9_\-]+)(?:\s*:\s*\"?([^\n\r\"]*)\"?)?",
    re.MULTILINE,
)


def _clean_label(raw: str) -> str:
    """Limpia etiquetas quitando saltos de línea, etiquetas HTML y espacios redundantes."""
    if not raw:
        return ""
    # Decodificar entidades HTML y despojar etiquetas <...>
    text = html.unescape(raw)
    text = re.sub(r"<[^>]+>", " ", text)
    # Reemplazar saltos de línea literales \n
    text = text.replace(r"\n", " ").replace("\n", " ").replace("\r", " ")
    # Quitar comillas o paréntesis residuales en los extremos
    text = " ".join(text.split()).strip()
    return text


class DiagramConnector(BaseConnector):
    """
    Conector de diagramas arquitectónicos multiformato (PlantUML, Archi, draw.io).
    """

    name: str = "DiagramConnector"
    supported_extensions: List[str] = [".puml", ".drawio", ".archimate", ".xml"]

    def can_handle(self, path: Union[str, Path]) -> bool:
        p = Path(path)
        if p.is_dir():
            return False

        ext = p.suffix.lower()
        if ext in [".puml", ".drawio", ".archimate"]:
            return True

        if ext == ".xml":
            # Inspeccionar el encabezado del archivo XML para detectar formato draw.io o Archi
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    snippet = f.read(2048)
                    if "<mxfile" in snippet or "<mxGraphModel" in snippet:
                        return True
                    if "<archimate:" in snippet or "archimatetool.com" in snippet or "opengroup.org/xsd/archimate" in snippet:
                        return True
                    if "<model" in snippet and ("element" in snippet or "ApplicationComponent" in snippet):
                        return True
            except Exception:
                return False

        return False

    def extract(self, path: Union[str, Path]) -> List[EvidenciaDiagrama]:
        """
        Extrae componentes, relaciones y citas desde el diagrama.
        """
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Archivo de diagrama no encontrado: {path}")

        ext = p.suffix.lower()
        if ext == ".puml":
            return [self._parse_plantuml(p)]
        elif ext == ".drawio":
            return [self._parse_drawio(p)]
        elif ext == ".archimate":
            return [self._parse_archi_xml(p)]
        elif ext == ".xml":
            # Detectar si es draw.io o Archi XML
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                snippet = f.read(2048)
            if "<mxfile" in snippet or "<mxGraphModel" in snippet:
                return [self._parse_drawio(p)]
            else:
                return [self._parse_archi_xml(p)]
        else:
            raise ValueError(f"Extensión de diagrama no soportada: {ext}")

    def _parse_plantuml(self, path: Path) -> EvidenciaDiagrama:
        """Parsea elementos y relaciones en especificaciones PlantUML / ArchiMate."""
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            raise RuntimeError(f"Error al leer archivo PlantUML {path}: {e}")

        lines = content.splitlines()
        id_to_name: Dict[str, str] = {}
        components_set: Set[str] = set()
        relations: List[Dict[str, str]] = []
        citations: Dict[str, str] = {}

        # 1. Parsear elementos de macros (ej: Application_Component(id, "Nombre"))
        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("'") or stripped.startswith("/'"):
                continue

            # Buscar macros ArchiMate / C4
            m = PLANTUML_MACRO_PATTERN.match(line)
            if m:
                macro_type, elem_id, raw_label = m.group(1), m.group(2), m.group(3)
                clean_name = _clean_label(raw_label)
                if not clean_name:
                    clean_name = elem_id
                id_to_name[elem_id] = clean_name
                components_set.add(clean_name)
                citations[f"{path.name}#L{line_no}"] = f"{macro_type}({elem_id}, \"{clean_name}\")"
                continue

            # Buscar componentes estándar: component "Nombre" as id
            m_std = PLANTUML_STD_COMPONENT.match(line)
            if m_std:
                raw_label, elem_id = m_std.group(1), m_std.group(2)
                clean_name = _clean_label(raw_label)
                key = elem_id if elem_id else clean_name
                id_to_name[key] = clean_name
                components_set.add(clean_name)
                citations[f"{path.name}#L{line_no}"] = f"Component \"{clean_name}\""
                continue

            # Buscar relaciones tipo macro: Rel_Serving(src, tgt, "label")
            m_rel = PLANTUML_REL_MACRO.match(line)
            if m_rel:
                rel_macro, src_id, tgt_id, rel_label = m_rel.group(1), m_rel.group(2), m_rel.group(3), m_rel.group(4) or ""
                src_name = id_to_name.get(src_id, src_id)
                tgt_name = id_to_name.get(tgt_id, tgt_id)
                rel_type = _clean_label(rel_label) if rel_label else rel_macro.replace("Rel_", "")
                relations.append({
                    "source": src_name,
                    "target": tgt_name,
                    "relation_type": rel_type,
                })
                citations[f"{path.name}#L{line_no}"] = f"{rel_macro}: {src_name} -> {tgt_name} ({rel_type})"
                continue

            # Buscar relaciones estándar con flechas: src --> tgt : label
            m_arrow = PLANTUML_REL_ARROW.match(line)
            if m_arrow:
                src_id, arrow, tgt_id, arrow_label = m_arrow.group(1), m_arrow.group(2), m_arrow.group(3), m_arrow.group(4) or ""
                # Descartar falsos positivos de líneas de comentarios o separadores
                if src_id in ["-", "=", "*"] or tgt_id in ["-", "=", "*"]:
                    continue
                src_name = id_to_name.get(src_id, src_id)
                tgt_name = id_to_name.get(tgt_id, tgt_id)
                rel_type = _clean_label(arrow_label) if arrow_label else f"Conexión {arrow}"
                relations.append({
                    "source": src_name,
                    "target": tgt_name,
                    "relation_type": rel_type,
                })
                citations[f"{path.name}#L{line_no}"] = f"Arrow {src_name} {arrow} {tgt_name} : {rel_type}"

        return EvidenciaDiagrama(
            source_file=path.name,
            format_type="PlantUML",
            components=sorted(list(components_set)),
            relations=relations,
            citations=citations,
        )

    def _parse_archi_xml(self, path: Path) -> EvidenciaDiagrama:
        """Parsea modelos de arquitectura Archi XML y Open Exchange Format."""
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except Exception as e:
            raise RuntimeError(f"Error al parsear XML de Archi {path}: e")

        id_to_name: Dict[str, str] = {}
        components_set: Set[str] = set()
        relations: List[Dict[str, str]] = []
        citations: Dict[str, str] = {}

        IGNORED_TAGS = {"model", "folder", "archimatemodel", "view", "diagram", "property", "documentation", "bounds", "location"}

        # 1. Recorrer elementos del modelo
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag.lower() in IGNORED_TAGS:
                continue

            attrib = elem.attrib

            elem_id = attrib.get("id") or attrib.get("identifier")
            elem_type = attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type") or attrib.get("xsi:type") or attrib.get("type") or tag
            elem_name = attrib.get("name")

            if not elem_name:
                # Buscar subelemento <name>
                for child in elem:
                    child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if child_tag == "name" and child.text:
                        elem_name = child.text
                        break

            # Identificar si es un componente de aplicación o elemento relevante
            is_relation = "relationship" in elem_type.lower() or "relationship" in tag.lower() or "relation" in tag.lower()
            if elem_id and elem_name and not is_relation:
                clean_name = _clean_label(elem_name)
                id_to_name[elem_id] = clean_name
                components_set.add(clean_name)
                citations[f"{path.name}#element/{elem_id}"] = f"{elem_type}: {clean_name}"

        # 2. Recorrer relaciones
        for elem in root.iter():
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            attrib = elem.attrib
            rel_id = attrib.get("id") or attrib.get("identifier") or f"rel_{len(relations)}"
            elem_type = attrib.get("{http://www.w3.org/2001/XMLSchema-instance}type") or attrib.get("xsi:type") or attrib.get("type") or tag
            src_id = attrib.get("source") or attrib.get("sourceAttachment")
            tgt_id = attrib.get("target") or attrib.get("targetAttachment")

            if src_id and tgt_id:
                src_name = id_to_name.get(src_id, src_id)
                tgt_name = id_to_name.get(tgt_id, tgt_id)

                rel_name = attrib.get("name")
                if not rel_name:
                    for child in elem:
                        child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                        if child_tag == "name" and child.text:
                            rel_name = child.text
                            break

                rel_type = _clean_label(rel_name) if rel_name else elem_type.replace("archimate:", "").replace("Relationship", "")
                relations.append({
                    "source": src_name,
                    "target": tgt_name,
                    "relation_type": rel_type,
                })
                citations[f"{path.name}#relationship/{rel_id}"] = f"{src_name} -> {tgt_name} ({rel_type})"

        return EvidenciaDiagrama(
            source_file=path.name,
            format_type="Archi XML",
            components=sorted(list(components_set)),
            relations=relations,
            citations=citations,
        )

    def _parse_drawio(self, path: Path) -> EvidenciaDiagrama:
        """Parsea esquemas y diagramas en draw.io XML (mxfile / mxGraphModel)."""
        try:
            tree = ET.parse(path)
            root = tree.getroot()
        except Exception as e:
            raise RuntimeError(f"Error al parsear draw.io XML {path}: {e}")

        id_to_name: Dict[str, str] = {}
        components_set: Set[str] = set()
        relations: List[Dict[str, str]] = []
        citations: Dict[str, str] = {}

        # 1. Identificar todas las celdas (mxCell)
        cells = [elem for elem in root.iter() if elem.tag.endswith("mxCell")]

        for cell in cells:
            cell_id = cell.attrib.get("id")
            val = cell.attrib.get("value", "")
            is_edge = cell.attrib.get("edge") == "1"

            if not cell_id or is_edge:
                continue

            clean_name = _clean_label(val)
            # Ignorar celdas estructurales raíz sin texto (0 y 1)
            if clean_name and cell_id not in ["0", "1"]:
                id_to_name[cell_id] = clean_name
                components_set.add(clean_name)
                citations[f"{path.name}#cell/{cell_id}"] = f"Componente: {clean_name}"

        # 2. Identificar relaciones/aristas (edge="1")
        for cell in cells:
            cell_id = cell.attrib.get("id")
            is_edge = cell.attrib.get("edge") == "1"
            src_id = cell.attrib.get("source")
            tgt_id = cell.attrib.get("target")

            if is_edge and src_id and tgt_id:
                edge_val = cell.attrib.get("value", "")
                src_name = id_to_name.get(src_id, src_id)
                tgt_name = id_to_name.get(tgt_id, tgt_id)
                rel_type = _clean_label(edge_val) if edge_val else "Conexión draw.io"

                relations.append({
                    "source": src_name,
                    "target": tgt_name,
                    "relation_type": rel_type,
                })
                citations[f"{path.name}#cell/{cell_id}"] = f"Edge: {src_name} -> {tgt_name} ({rel_type})"

        return EvidenciaDiagrama(
            source_file=path.name,
            format_type="draw.io",
            components=sorted(list(components_set)),
            relations=relations,
            citations=citations,
        )
