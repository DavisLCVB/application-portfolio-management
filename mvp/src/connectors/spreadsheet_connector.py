"""
Conector federado para catálogos y hojas de cálculo (.csv, .xlsx).

Permite ingerir inventarios existentes de aplicaciones, catálogos de activos TI
y matrices de responsables en formatos tabulares estándar, extrayendo
EvidenciaTecnica con citas de fila canónicas (ej. catalogo.xlsx#Sheet1!R12).
Implementado completamente en la biblioteca estándar de Python (zipfile + ElementTree).
"""

import csv
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..models import EvidenciaTecnica
from .base import BaseConnector


def _normalize_text(text: str) -> str:
    """Normaliza texto eliminando acentos y convirtiendo a minúsculas."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).strip().lower()


def _col_to_index(col_str: str) -> int:
    """Convierte letras de columna de Excel (ej. 'A', 'Z', 'AA') a índice 0-based."""
    idx = 0
    for char in col_str.upper():
        if "A" <= char <= "Z":
            idx = idx * 26 + (ord(char) - ord("A") + 1)
    return max(0, idx - 1)


class SpreadsheetConnector(BaseConnector):
    """
    Conector para procesar catálogos en CSV y Excel OpenXML (.xlsx).
    """

    name: str = "SpreadsheetConnector"
    supported_extensions: List[str] = [".csv", ".xlsx"]

    def can_handle(self, path: Union[str, Path]) -> bool:
        p = Path(path)
        if p.is_dir():
            return False
        return p.suffix.lower() in [ext.lower() for ext in self.supported_extensions]

    def extract(self, path: Union[str, Path]) -> List[EvidenciaTecnica]:
        """
        Extrae evidencias técnicas desde un archivo .csv o .xlsx.
        """
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Archivo no encontrado: {path}")

        suffix = p.suffix.lower()
        if suffix == ".csv":
            rows = self._read_csv(p)
            sheet_name = "CSV"
        elif suffix == ".xlsx":
            rows, sheet_name = self._read_xlsx(p)
        else:
            raise ValueError(f"Extensión no soportada por SpreadsheetConnector: {suffix}")

        if not rows:
            return []

        return self._parse_rows_to_evidence(rows, p.name, sheet_name)

    def _read_csv(self, path: Path) -> List[List[str]]:
        """Lee archivo CSV probando codificaciones comunes y detectando delimitadores."""
        encodings = ["utf-8-sig", "utf-8", "latin-1", "cp1252"]
        content: Optional[str] = None
        for enc in encodings:
            try:
                with open(path, "r", encoding=enc) as f:
                    content = f.read()
                break
            except (UnicodeDecodeError, LookupError):
                continue

        if content is None:
            return []

        # Detectar delimitador: coma, punto y coma o tabulación
        first_line = content.split("\n", 1)[0] if content else ""
        delimiter = ","
        if first_line.count(";") > first_line.count(","):
            delimiter = ";"
        elif first_line.count("\t") > first_line.count(","):
            delimiter = "\t"

        reader = csv.reader(content.splitlines(), delimiter=delimiter)
        return [[cell.strip() for cell in row] for row in reader if any(cell.strip() for cell in row)]

    def _read_xlsx(self, path: Path) -> Tuple[List[List[str]], str]:
        """
        Lee archivo .xlsx usando zipfile y ElementTree sin librerías externas.
        Procesa sharedStrings.xml y la primera hoja en worksheets/.
        """
        shared_strings: List[str] = []
        sheet_name = "Sheet1"
        rows: List[List[str]] = []

        with zipfile.ZipFile(path, "r") as zf:
            namelist = zf.namelist()

            # 1. Cargar strings compartidos si existen
            if "xl/sharedStrings.xml" in namelist:
                try:
                    tree = ET.fromstring(zf.read("xl/sharedStrings.xml"))
                    for si in tree:
                        # Un elemento <si> puede tener <t> directo o <r><t>
                        texts = [elem.text for elem in si.iter() if elem.tag.endswith("t") and elem.text]
                        shared_strings.append("".join(texts))
                except Exception:
                    shared_strings = []

            # 2. Identificar la primera hoja de trabajo
            sheet_files = [f for f in sorted(namelist) if f.startswith("xl/worksheets/sheet") and f.endswith(".xml")]
            if not sheet_files:
                return [], sheet_name

            target_sheet_file = sheet_files[0]
            # Determinar nombre aproximado de hoja
            sheet_match = re.search(r"sheet(\d+)\.xml", target_sheet_file)
            if sheet_match:
                sheet_name = f"Sheet{sheet_match.group(1)}"

            # 3. Parsear celdas de la hoja
            tree = ET.fromstring(zf.read(target_sheet_file))
            sheet_data = None
            for elem in tree.iter():
                if elem.tag.endswith("sheetData"):
                    sheet_data = elem
                    break

            if sheet_data is None:
                return [], sheet_name

            for row_elem in sheet_data:
                if not row_elem.tag.endswith("row"):
                    continue

                row_cells: Dict[int, str] = {}
                max_col = 0
                for c in row_elem:
                    if not c.tag.endswith("c"):
                        continue
                    ref = c.attrib.get("r", "")
                    col_match = re.match(r"([A-Za-z]+)(\d+)", ref)
                    col_idx = _col_to_index(col_match.group(1)) if col_match else len(row_cells)
                    cell_type = c.attrib.get("t", "")

                    val = ""
                    # Caso inline string <is><t>
                    inline_t = c.find(".//{*}t")
                    if inline_t is not None and inline_t.text:
                        val = inline_t.text
                    else:
                        v_elem = None
                        for child in c:
                            if child.tag.endswith("v"):
                                v_elem = child
                                break
                        if v_elem is not None and v_elem.text is not None:
                            raw_val = v_elem.text
                            if cell_type == "s":
                                try:
                                    s_idx = int(raw_val)
                                    val = shared_strings[s_idx] if s_idx < len(shared_strings) else raw_val
                                except (ValueError, IndexError):
                                    val = raw_val
                            elif cell_type == "b":
                                val = "VERDADERO" if raw_val == "1" else "FALSO"
                            else:
                                val = raw_val

                    row_cells[col_idx] = val.strip()
                    if col_idx > max_col:
                        max_col = col_idx

                if row_cells:
                    row_list = [row_cells.get(i, "") for i in range(max_col + 1)]
                    rows.append(row_list)

        return rows, sheet_name

    def _parse_rows_to_evidence(
        self, rows: List[List[str]], file_name: str, sheet_name: str
    ) -> List[EvidenciaTecnica]:
        """Identifica columnas semánticas y mapea cada fila de datos a EvidenciaTecnica."""
        if not rows:
            return []

        # Buscar fila de cabecera (primera fila con al menos 2 celdas no vacías)
        header_idx = -1
        for i, row in enumerate(rows):
            non_empty = [c for c in row if c]
            if len(non_empty) >= 2:
                header_idx = i
                break

        if header_idx == -1:
            return []

        header = rows[header_idx]
        col_mapping = self._identify_columns(header)

        evidences: List[EvidenciaTecnica] = []

        for row_offset, row in enumerate(rows[header_idx + 1 :]):
            row_num = header_idx + 2 + row_offset
            if not any(row):
                continue

            app_name = self._get_col_val(row, col_mapping.get("name"))
            if not app_name:
                # Si no hay nombre de aplicación explícito, intentar usar el primer campo no vacío
                candidates = [c for c in row if c]
                if candidates:
                    app_name = candidates[0]
                else:
                    continue

            tech_val = self._get_col_val(row, col_mapping.get("tech"))
            owner_val = self._get_col_val(row, col_mapping.get("owner")) or "Desconocido"
            runtime_val = self._get_col_val(row, col_mapping.get("runtime"))
            deps_val = self._get_col_val(row, col_mapping.get("deps"))
            sla_val = self._get_col_val(row, col_mapping.get("sla"))
            provider_val = self._get_col_val(row, col_mapping.get("provider"))

            # Determinar lenguaje principal
            primary_language = self._infer_language(tech_val, app_name)
            runtime_version = runtime_val or self._infer_runtime_version(tech_val)

            # Dependencias
            dependencies: List[str] = []
            if deps_val:
                dependencies = [d.strip() for d in re.split(r"[,;|\n]+", deps_val) if d.strip()]

            # Construir cita de evidencia primaria
            citation_loc = f"{file_name}#{sheet_name}!R{row_num}" if sheet_name != "CSV" else f"{file_name}#R{row_num}"
            citation_detail = f"Fila {row_num}: {app_name}"
            if tech_val:
                citation_detail += f" | Stack: {tech_val}"
            if owner_val != "Desconocido":
                citation_detail += f" | Responsable: {owner_val}"
            if sla_val:
                citation_detail += f" | SLA: {sla_val}"
            if provider_val:
                citation_detail += f" | Proveedor: {provider_val}"

            citations = {
                citation_loc: citation_detail
            }

            ev = EvidenciaTecnica(
                repo_name=app_name,
                commit_hash=f"spreadsheet-{Path(file_name).stem}",
                primary_language=primary_language,
                runtime_version=runtime_version,
                dependencies=dependencies,
                endpoints=[],
                top_contributor=owner_val,
                file_citations=citations,
            )
            evidences.append(ev)

        return evidences

    def _identify_columns(self, header: List[str]) -> Dict[str, int]:
        """Mapea tipos de columnas a índices en base a heurísticas léxicas."""
        mapping: Dict[str, int] = {}
        for idx, col in enumerate(header):
            norm = _normalize_text(col)
            if any(k in norm for k in ["nombre", "aplicacion", "sistema", "app", "servicio", "software"]) and "name" not in mapping:
                mapping["name"] = idx
            elif any(k in norm for k in ["propietario", "responsable", "owner", "lider", "contacto", "equipo"]) and "owner" not in mapping:
                mapping["owner"] = idx
            elif any(k in norm for k in ["lenguaje", "tecnologia", "stack", "plataforma", "framework", "arquitectura"]) and "tech" not in mapping:
                mapping["tech"] = idx
            elif any(k in norm for k in ["runtime", "version runtime", "version", "versión"]) and "runtime" not in mapping:
                mapping["runtime"] = idx
            elif any(k in norm for k in ["dependencia", "libreria", "modulo", "paquete", "componentes"]) and "deps" not in mapping:
                mapping["deps"] = idx
            elif any(k in norm for k in ["sla", "disponibilidad", "uptime"]) and "sla" not in mapping:
                mapping["sla"] = idx
            elif any(k in norm for k in ["proveedor", "contratista", "empresa", "vendor"]) and "provider" not in mapping:
                mapping["provider"] = idx

        # Si no se encontró columna 'name', usar la primera columna que contenga 'id' o la columna 0/1
        if "name" not in mapping:
            for idx, col in enumerate(header):
                norm = _normalize_text(col)
                if "id" in norm or "codigo" in norm:
                    mapping["name"] = idx
                    break
            if "name" not in mapping and header:
                mapping["name"] = 0

        return mapping

    def _get_col_val(self, row: List[str], idx: Optional[int]) -> str:
        if idx is not None and 0 <= idx < len(row):
            return row[idx].strip()
        return ""

    def _infer_language(self, tech_text: str, fallback_text: str) -> str:
        text = f"{tech_text} {fallback_text}".lower()
        if "java" in text or "spring" in text or "maven" in text:
            return "Java"
        if "typescript" in text or "ts" in text:
            return "TypeScript"
        if "javascript" in text or "node" in text or "react" in text or "angular" in text or "vue" in text:
            return "JavaScript / TypeScript"
        if "python" in text or "fastapi" in text or "django" in text or "flask" in text:
            return "Python"
        if "c#" in text or ".net" in text or "csharp" in text:
            return "C# / .NET"
        if "go" in text or "golang" in text:
            return "Go"
        if "php" in text or "laravel" in text:
            return "PHP"
        if "ruby" in text or "rails" in text:
            return "Ruby"
        return tech_text if tech_text else "Desconocido"

    def _infer_runtime_version(self, tech_text: str) -> str:
        if not tech_text:
            return "N/A"
        version_match = re.search(r"(\d+(?:\.\d+)+)", tech_text)
        if version_match:
            return version_match.group(1)
        return "N/A"
