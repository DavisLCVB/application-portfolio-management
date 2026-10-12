"""
Suite de pruebas unitarias para la Capa de Conectores Federados Multimodales.

Prueba la ingesta y extracción trazable desde:
- Hojas de cálculo y catálogos (CSV y XLSX con SpreadsheetConnector)
- Presentaciones de arquitectura (PPTX con PresentationConnector)
- Diagramas y modelos técnicos (PlantUML, Archi XML, draw.io XML con DiagramConnector)
- Registro federado y escaneo de directorios (ConnectorRegistry)
"""

import json
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from src.connectors.base import BaseConnector
from src.connectors.diagram_connector import DiagramConnector
from src.connectors.presentation_connector import PresentationConnector
from src.connectors.registry import (
    CodeToCatalogConnector,
    ConnectorRegistry,
    ContractMinerConnector,
)
from src.connectors.spreadsheet_connector import SpreadsheetConnector
from src.models import EvidenciaContractual, EvidenciaDiagrama, EvidenciaTecnica

TESTS_DIR = Path(__file__).resolve().parent
MVP_DIR = TESTS_DIR.parent
ROOT_DIR = MVP_DIR.parent
FIXTURES_DIR = MVP_DIR / "fixtures"


def _create_minimal_xlsx(file_path: Path, rows: list) -> None:
    """Genera un archivo .xlsx OpenXML mínimo y válido usando únicamente zipfile y XML estándar."""
    # Construir sharedStrings
    unique_strings = []
    string_map = {}
    for row in rows:
        for cell in row:
            s = str(cell)
            if s not in string_map:
                string_map[s] = len(unique_strings)
                unique_strings.append(s)

    # 1. sharedStrings.xml
    sst_root = ET.Element("sst", {
        "xmlns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "count": str(len(unique_strings)),
        "uniqueCount": str(len(unique_strings)),
    })
    for s in unique_strings:
        si = ET.SubElement(sst_root, "si")
        t = ET.SubElement(si, "t")
        t.text = s
    sst_xml = ET.tostring(sst_root, encoding="utf-8", xml_declaration=True)

    # 2. sheet1.xml
    ws_root = ET.Element("worksheet", {
        "xmlns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    })
    sheet_data = ET.SubElement(ws_root, "sheetData")
    for r_idx, row in enumerate(rows, start=1):
        row_elem = ET.SubElement(sheet_data, "row", {"r": str(r_idx)})
        for c_idx, cell in enumerate(row):
            col_letter = chr(ord("A") + c_idx)
            c_elem = ET.SubElement(row_elem, "c", {
                "r": f"{col_letter}{r_idx}",
                "t": "s",
            })
            v_elem = ET.SubElement(c_elem, "v")
            v_elem.text = str(string_map[str(cell)])
    sheet_xml = ET.tostring(ws_root, encoding="utf-8", xml_declaration=True)

    # 3. [Content_Types].xml
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>
</Types>"""

    # 4. _rels/.rels
    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

    # 5. xl/workbook.xml
    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Sheet1" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""

    # 6. xl/_rels/workbook.xml.rels
    wb_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>
</Relationships>"""

    with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/sharedStrings.xml", sst_xml)
        zf.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def _create_minimal_pptx(file_path: Path, slide_text: str, shape_id: str = "2") -> None:
    """Genera un archivo .pptx OpenXML sintético con una diapositiva y una forma con texto."""
    slide_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr/>
      <p:sp>
        <p:nvSpPr>
          <p:cNvPr id="{shape_id}" name="Title {shape_id}"/>
          <p:cNvSpPr/>
          <p:nvPr/>
        </p:nvSpPr>
        <p:spPr/>
        <p:txBody>
          <a:bodyPr/>
          <a:lstStyle/>
          <a:p>
            <a:r>
              <a:t>{slide_text}</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
</p:sld>"""

    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
</Types>"""

    root_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"""

    presentation_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:sldIdLst>
    <p:sldId id="256" r:id="rId1"/>
  </p:sldIdLst>
</p:presentation>"""

    pres_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
</Relationships>"""

    with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("ppt/presentation.xml", presentation_xml)
        zf.writestr("ppt/_rels/presentation.xml.rels", pres_rels)
        zf.writestr("ppt/slides/slide1.xml", slide_xml)


class TestSpreadsheetConnector(unittest.TestCase):
    """Pruebas del conector de catálogos y hojas de cálculo (CSV y XLSX)."""

    def setUp(self):
        self.connector = SpreadsheetConnector()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_can_handle(self):
        self.assertTrue(self.connector.can_handle(Path("catalogo.csv")))
        self.assertTrue(self.connector.can_handle(Path("catalogo.xlsx")))
        self.assertFalse(self.connector.can_handle(Path("documento.docx")))
        self.assertFalse(self.connector.can_handle(Path("archivo.pdf")))

    def test_extract_csv_catalog(self):
        csv_file = FIXTURES_DIR / "catalogs" / "catalogo_aplicaciones.csv"
        self.assertTrue(csv_file.is_file(), f"Fixture no encontrado: {csv_file}")

        evidences = self.connector.extract(csv_file)
        self.assertEqual(len(evidences), 3)

        app1 = evidences[0]
        self.assertEqual(app1.repo_name, "Sistema Integrado de Tesorería")
        self.assertEqual(app1.primary_language, "Java")
        self.assertIn("cmendoza@mef.gob.pe", app1.top_contributor)
        self.assertTrue(any("catalogo_aplicaciones.csv#R2" in k for k in app1.file_citations))

        app2 = evidences[1]
        self.assertEqual(app2.repo_name, "Ventanilla Única de Trámites")
        self.assertEqual(app2.primary_language, "TypeScript")

        app3 = evidences[2]
        self.assertEqual(app3.repo_name, "Módulo de Conciliación Bancaria")
        self.assertEqual(app3.primary_language, "Python")

    def test_extract_xlsx_catalog(self):
        xlsx_file = self.temp_path / "test_catalogo.xlsx"
        rows = [
            ["ID", "Nombre Aplicación", "Responsable Técnico", "Tecnología", "SLA"],
            ["APP-101", "Servicio de Deuda Pública", "Elena Ramos <eramos@mef.gob.pe>", "Java Spring Boot 3.1", "99.9%"],
            ["APP-102", "Portal de Transparencia Económica", "Mario Ruiz <mruiz@mef.gob.pe>", "TypeScript React 18", "99.5%"],
        ]
        _create_minimal_xlsx(xlsx_file, rows)

        evidences = self.connector.extract(xlsx_file)
        self.assertEqual(len(evidences), 2)

        ev1 = evidences[0]
        self.assertEqual(ev1.repo_name, "Servicio de Deuda Pública")
        self.assertEqual(ev1.primary_language, "Java")
        self.assertEqual(ev1.runtime_version, "3.1")
        self.assertIn("eramos@mef.gob.pe", ev1.top_contributor)
        # Verificar formato canónico de cita OpenXML
        self.assertTrue(any("test_catalogo.xlsx#Sheet1!R2" in k for k in ev1.file_citations))


class TestPresentationConnector(unittest.TestCase):
    """Pruebas del conector de presentaciones ejecutivas y de arquitectura (.pptx)."""

    def setUp(self):
        self.connector = PresentationConnector()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_can_handle(self):
        self.assertTrue(self.connector.can_handle(Path("presentacion.pptx")))
        self.assertFalse(self.connector.can_handle(Path("modelo.archimate")))

    def test_extract_synthetic_pptx(self):
        pptx_file = self.temp_path / "arquitectura_test.pptx"
        text = "Sistema de Gestión de Planillas MEF implementado con Java Spring Boot y Docker. Contacto: dev@mef.gob.pe"
        _create_minimal_pptx(pptx_file, text, shape_id="4")

        evidences = self.connector.extract(pptx_file)
        self.assertGreaterEqual(len(evidences), 1)

        tech_ev = next((e for e in evidences if isinstance(e, EvidenciaTecnica)), None)
        self.assertIsNotNone(tech_ev)
        self.assertIn("Sistema de Gestión de Planillas", tech_ev.repo_name)
        self.assertEqual(tech_ev.primary_language, "Java")
        self.assertIn("dev@mef.gob.pe", tech_ev.top_contributor)
        self.assertTrue(any("Slide1!Shape4" in k for k in tech_ev.file_citations))

    def test_extract_existing_project_pptx(self):
        # Si existe GobIA_TF_Arquitectura_IA.pptx en la raíz del proyecto, probarlo
        project_pptx = ROOT_DIR / "GobIA_TF_Arquitectura_IA.pptx"
        if project_pptx.is_file():
            evidences = self.connector.extract(project_pptx)
            self.assertIsInstance(evidences, list)
            self.assertGreater(len(evidences), 0)
            # Debe contener evidencias técnicas o de diagrama
            has_valid_type = any(
                isinstance(e, (EvidenciaTecnica, EvidenciaDiagrama)) for e in evidences
            )
            self.assertTrue(has_valid_type)


class TestDiagramConnector(unittest.TestCase):
    """Pruebas del conector de diagramas (PlantUML, Archi XML, draw.io XML)."""

    def setUp(self):
        self.connector = DiagramConnector()

    def test_can_handle(self):
        self.assertTrue(self.connector.can_handle(Path("diag.puml")))
        self.assertTrue(self.connector.can_handle(Path("modelo.archimate")))
        self.assertTrue(self.connector.can_handle(Path("esquema.drawio")))
        self.assertTrue(self.connector.can_handle(FIXTURES_DIR / "diagrams" / "arquitectura_drawio.xml"))

    def test_extract_plantuml(self):
        puml_path = ROOT_DIR / "docs" / "arquitectura" / "diagramas" / "contexto.puml"
        self.assertTrue(puml_path.is_file(), f"Archivo no encontrado: {puml_path}")

        evidences = self.connector.extract(puml_path)
        self.assertEqual(len(evidences), 1)

        diag = evidences[0]
        self.assertIsInstance(diag, EvidenciaDiagrama)
        self.assertEqual(diag.format_type, "PlantUML")
        self.assertGreater(len(diag.components), 5)
        # Componente APM debe haber sido detectado
        self.assertTrue(any("Plataforma APM" in c for c in diag.components))
        # Relaciones deben haber sido detectadas
        self.assertGreater(len(diag.relations), 3)
        self.assertTrue(any(r["relation_type"] in ["Serving_Right", "Serving_Up", "Serving"] for r in diag.relations))
        # Citas con número de línea
        self.assertTrue(any("#L" in k for k in diag.citations))

    def test_extract_drawio_xml(self):
        drawio_file = FIXTURES_DIR / "diagrams" / "arquitectura_drawio.xml"
        self.assertTrue(drawio_file.is_file(), f"Fixture no encontrado: {drawio_file}")

        evidences = self.connector.extract(drawio_file)
        self.assertEqual(len(evidences), 1)

        diag = evidences[0]
        self.assertEqual(diag.format_type, "draw.io")
        self.assertEqual(len(diag.components), 4)
        self.assertIn("Portal del Contribuyente", diag.components)
        self.assertIn("Pasarela de Pagos Digitales", diag.components)
        self.assertIn("Servicio de Autenticación Central", diag.components)
        self.assertIn("Base de Datos de Transacciones", diag.components)

        # Verificar conexiones y resolución de nombres
        self.assertEqual(len(diag.relations), 3)
        edge1 = next((r for r in diag.relations if "Inicia transacción" in r["relation_type"]), None)
        self.assertIsNotNone(edge1)
        self.assertEqual(edge1["source"], "Portal del Contribuyente")
        self.assertEqual(edge1["target"], "Pasarela de Pagos Digitales")

        # Citas de celda
        self.assertTrue(any("arquitectura_drawio.xml#cell/node-portal" in k for k in diag.citations))

    def test_extract_archi_xml(self):
        archi_file = FIXTURES_DIR / "diagrams" / "modelo_archi.archimate"
        self.assertTrue(archi_file.is_file(), f"Fixture no encontrado: {archi_file}")

        evidences = self.connector.extract(archi_file)
        self.assertEqual(len(evidences), 1)

        diag = evidences[0]
        self.assertEqual(diag.format_type, "Archi XML")
        self.assertEqual(len(diag.components), 4)
        self.assertIn("Sistema Integrado de Gestión Financiera (SIGF)", diag.components)
        self.assertIn("Módulo de Tesorería Pública", diag.components)
        self.assertIn("Servicio de Interoperabilidad Bancaria", diag.components)
        self.assertIn("API Gateway Financiero", diag.components)

        # Relaciones
        self.assertEqual(len(diag.relations), 3)
        rel1 = next((r for r in diag.relations if r["relation_type"] == "compone"), None)
        self.assertIsNotNone(rel1)
        self.assertEqual(rel1["source"], "Sistema Integrado de Gestión Financiera (SIGF)")
        self.assertEqual(rel1["target"], "Módulo de Tesorería Pública")

        # Citas
        self.assertTrue(any("modelo_archi.archimate#element/elem-sigf" in k for k in diag.citations))


class TestConnectorRegistry(unittest.TestCase):
    """Pruebas del registro de conectores y orquestación federada."""

    def setUp(self):
        self.registry = ConnectorRegistry()

    def test_registered_defaults(self):
        names = [c.name for c in self.registry.registered_connectors]
        self.assertIn("SpreadsheetConnector", names)
        self.assertIn("PresentationConnector", names)
        self.assertIn("DiagramConnector", names)
        self.assertIn("CodeToCatalogConnector", names)
        self.assertIn("ContractMinerConnector", names)

    def test_scan_single_file_delegation(self):
        csv_file = FIXTURES_DIR / "catalogs" / "catalogo_aplicaciones.csv"
        evidences = self.registry.scan_file(csv_file)
        self.assertEqual(len(evidences), 3)
        self.assertTrue(all(isinstance(e, EvidenciaTecnica) for e in evidences))

    def test_scan_diagrams_directory(self):
        diagrams_dir = FIXTURES_DIR / "diagrams"
        evidences = self.registry.scan_directory(diagrams_dir)
        self.assertGreaterEqual(len(evidences), 2)
        diagram_evs = [e for e in evidences if isinstance(e, EvidenciaDiagrama)]
        self.assertGreaterEqual(len(diagram_evs), 2)

    def test_partition_evidences(self):
        ev_tec = EvidenciaTecnica(repo_name="app1", commit_hash="1", primary_language="Java", runtime_version="17")
        ev_cnt = EvidenciaContractual(doc_name="doc1", doc_id="TDR-1", provider_name="Prov1")
        ev_diag = EvidenciaDiagrama(source_file="d.puml", format_type="PlantUML")

        part = ConnectorRegistry.partition_evidences([ev_tec, ev_cnt, ev_diag])
        self.assertEqual(len(part["tecnica"]), 1)
        self.assertEqual(len(part["contractual"]), 1)
        self.assertEqual(len(part["diagrama"]), 1)


if __name__ == "__main__":
    unittest.main()
