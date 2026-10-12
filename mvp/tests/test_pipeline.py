"""
Pruebas unitarias e integrales para el Pipeline de Descubrimiento Continuo (MVP 1).

Cubre:
- Modelos de datos canónicos y serialización.
- Extractor Code-to-Catalog (Maven, npm, Dockerfile, endpoints, git).
- Minero documental Dark Data Miner (TDRs, regex estructurado, cláusulas).
- Reconciliador semántico (score heurístico, similitud difusa, LeanIX Fact Sheets).
- Generador de micro-nudges (Adaptive Cards, acciones en 1 clic).
- Pipeline end-to-end y generación de artefactos JSON.
"""

import json
import os
import sys
import unittest
from pathlib import Path

# Configurar path para permitir ejecución directa o vía runner
MVP_DIR = Path(__file__).resolve().parent.parent
if str(MVP_DIR) not in sys.path:
    sys.path.insert(0, str(MVP_DIR))

from src.code_to_catalog import CodeToCatalogExtractor
from src.contract_miner import ContractMiner
from src.models import (
    EvidenciaContractual,
    EvidenciaTecnica,
    HipotesisFactSheet,
    MicroNudge,
)
from src.nudge_generator import NudgeGenerator
from src.reconciliator import SemanticReconciliator
import run_discovery


class TestModels(unittest.TestCase):
    """Pruebas de modelos de datos canónicos."""

    def test_evidencia_tecnica_to_dict(self):
        ev = EvidenciaTecnica(
            repo_name="demo-repo",
            commit_hash="abc123456789",
            primary_language="Java",
            runtime_version="Java 17",
            dependencies=["spring-boot-starter-web"],
            endpoints=["GET /api/v1/test"],
            top_contributor="Dev Team <dev@test.com>",
            file_citations={"pom.xml": "L10"},
        )
        data = ev.to_dict()
        self.assertEqual(data["repo_name"], "demo-repo")
        self.assertEqual(data["primary_language"], "Java")
        self.assertIn("spring-boot-starter-web", data["dependencies"])
        self.assertEqual(data["file_citations"]["pom.xml"], "L10")

    def test_evidencia_contractual_to_dict(self):
        cev = EvidenciaContractual(
            doc_name="TDR Contrato de Pruebas",
            doc_id="TDR-2024-TEST-001",
            provider_name="Empresa Proveedora S.A.",
            contract_dates={"start_date": "2024-01-01", "end_date": "2025-12-31"},
            sla_uptime="99.9%",
            acquired_licenses=["PostgreSQL", "Java"],
            doc_citations={"provider": "Cláusula 2"},
        )
        data = cev.to_dict()
        self.assertEqual(data["doc_id"], "TDR-2024-TEST-001")
        self.assertEqual(data["sla_uptime"], "99.9%")
        self.assertEqual(len(data["acquired_licenses"]), 2)

    def test_hipotesis_fact_sheet_to_dict(self):
        h = HipotesisFactSheet(
            entity_name="Servicio Pagos",
            candidate_type="Application",
            technical_stack="Java (Java 17)",
            provider="Indra Soluciones",
            sla_uptime="99.9%",
            confidence_score=0.92,
            status="Draft",
            primary_citations=[{"source": "code", "file": "pom.xml#L10"}],
        )
        data = h.to_dict()
        self.assertEqual(data["entity_name"], "Servicio Pagos")
        self.assertEqual(data["confidence_score"], 0.92)
        self.assertEqual(data["status"], "Draft")


class TestCodeToCatalogExtractor(unittest.TestCase):
    """Pruebas del Agente Code-to-Catalog."""

    def setUp(self):
        self.extractor = CodeToCatalogExtractor()
        self.fixtures_dir = MVP_DIR / "fixtures"

    def test_extract_java_maven_repo(self):
        repo_path = self.fixtures_dir / "repo-recaudacion"
        ev = self.extractor.extract(str(repo_path))

        self.assertEqual(ev.repo_name, "recaudacion-digital-service")
        self.assertEqual(ev.primary_language, "Java")
        self.assertIn("17", ev.runtime_version)
        self.assertIn("spring-boot-starter-web", ev.dependencies)
        self.assertIn("postgresql", ev.dependencies)
        self.assertTrue(len(ev.endpoints) >= 2)
        self.assertTrue(any("recaudacion/pagos" in ep for ep in ev.endpoints))
        self.assertIn("dependencies", ev.file_citations)
        self.assertIn("dockerfile_base", ev.file_citations)
        self.assertTrue(len(ev.commit_hash) >= 8)

    def test_extract_node_repo(self):
        repo_path = self.fixtures_dir / "repo-portal-atencion"
        ev = self.extractor.extract(str(repo_path))

        self.assertEqual(ev.repo_name, "portal-atencion-ciudadano")
        self.assertIn("JavaScript", ev.primary_language)
        self.assertIn("express", ev.dependencies)
        self.assertIn("next", ev.dependencies)
        self.assertTrue(len(ev.endpoints) >= 2)
        self.assertTrue(any("atencion/tickets" in ep for ep in ev.endpoints))
        self.assertIn("dependencies", ev.file_citations)
        self.assertIn("dockerfile_base", ev.file_citations)

    def test_invalid_repo_path_raises_error(self):
        with self.assertRaises(FileNotFoundError):
            self.extractor.extract("/ruta/inexistente/repo-xyz")


class TestContractMiner(unittest.TestCase):
    """Pruebas del Agente Dark Data Miner."""

    def setUp(self):
        self.miner = ContractMiner()
        self.contracts_dir = MVP_DIR / "fixtures" / "contracts"

    def test_extract_recaudacion_tdr(self):
        tdr_path = self.contracts_dir / "tdr-recaudacion-digital.md"
        ev = self.miner.extract(str(tdr_path))

        self.assertEqual(ev.doc_id, "TDR-2024-MEF-0089")
        self.assertIn("Indra Soluciones", ev.provider_name)
        self.assertEqual(ev.sla_uptime, "99.9%")
        self.assertEqual(ev.contract_dates.get("start_date"), "2024-03-01")
        self.assertEqual(ev.contract_dates.get("end_date"), "2026-02-28")
        self.assertIn("PostgreSQL", ev.acquired_licenses)
        self.assertIn("Spring Boot", ev.acquired_licenses)
        self.assertIn("provider", ev.doc_citations)
        self.assertIn("sla_uptime", ev.doc_citations)

    def test_extract_portal_ciudadano_tdr(self):
        tdr_path = self.contracts_dir / "tdr-portal-ciudadano.md"
        ev = self.miner.extract(str(tdr_path))

        self.assertEqual(ev.doc_id, "TDR-2023-MEF-0145")
        self.assertIn("Stefanini IT", ev.provider_name)
        self.assertEqual(ev.sla_uptime, "99.5%")
        self.assertEqual(ev.contract_dates.get("start_date"), "2023-11-01")
        self.assertEqual(ev.contract_dates.get("end_date"), "2025-10-31")
        self.assertIn("Node.js", ev.acquired_licenses)
        self.assertIn("React", ev.acquired_licenses)


class TestSemanticReconciliator(unittest.TestCase):
    """Pruebas del Agente Reconciliador Semántico."""

    def setUp(self):
        self.reconciliator = SemanticReconciliator(review_threshold=0.85)
        extractor = CodeToCatalogExtractor()
        miner = ContractMiner()

        self.tech_recaudacion = extractor.extract(str(MVP_DIR / "fixtures" / "repo-recaudacion"))
        self.tech_portal = extractor.extract(str(MVP_DIR / "fixtures" / "repo-portal-atencion"))

        self.contract_recaudacion = miner.extract(str(MVP_DIR / "fixtures" / "contracts" / "tdr-recaudacion-digital.md"))
        self.contract_portal = miner.extract(str(MVP_DIR / "fixtures" / "contracts" / "tdr-portal-ciudadano.md"))

    def test_matching_recaudacion_scores_higher_than_mismatch(self):
        score_correct = self.reconciliator.compute_confidence(self.tech_recaudacion, self.contract_recaudacion)
        score_mismatch = self.reconciliator.compute_confidence(self.tech_recaudacion, self.contract_portal)

        self.assertGreater(score_correct, 0.75)
        self.assertGreater(score_correct, score_mismatch)

    def test_matching_portal_scores_higher_than_mismatch(self):
        score_correct = self.reconciliator.compute_confidence(self.tech_portal, self.contract_portal)
        score_mismatch = self.reconciliator.compute_confidence(self.tech_portal, self.contract_recaudacion)

        self.assertGreater(score_correct, 0.70)
        self.assertGreater(score_correct, score_mismatch)

    def test_reconcile_pair_produces_valid_hipotesis(self):
        hipotesis = self.reconciliator.reconcile_pair(self.tech_recaudacion, self.contract_recaudacion)

        self.assertEqual(hipotesis.candidate_type, "Application")
        self.assertIn("Java", hipotesis.technical_stack)
        self.assertIn("Indra", hipotesis.provider)
        self.assertEqual(hipotesis.sla_uptime, "99.9%")
        self.assertTrue(len(hipotesis.primary_citations) > 0)

    def test_match_all_pairs_correctly(self):
        result = self.reconciliator.match_all(
            [self.tech_recaudacion, self.tech_portal],
            [self.contract_recaudacion, self.contract_portal]
        )
        # Solo se vinculan los pares que superan el score mínimo (sin forzar cruces)
        pairs = {(tech.repo_name, contract.doc_id) for _, tech, contract in result.links}
        self.assertEqual(pairs, {
            ("recaudacion-digital-service", "TDR-2024-MEF-0089"),
            ("portal-atencion-ciudadano", "TDR-2023-MEF-0145"),
        })
        self.assertEqual(result.orphans, [])


class TestNudgeGenerator(unittest.TestCase):
    """Pruebas del Agente Micro-Nudge."""

    def setUp(self):
        self.generator = NudgeGenerator(review_threshold=0.85)

    def test_generates_nudge_for_missing_business_owner(self):
        hipotesis = HipotesisFactSheet(
            entity_name="Sistema de Recaudación",
            candidate_type="Application",
            technical_stack="Java 17",
            provider="Indra Soluciones",
            sla_uptime="99.9%",
            confidence_score=0.90,
            status="Draft",
            business_owner=None,  # Campo faltante
            technical_owner="Dev Lead <dev@mef.gob.pe>",
        )
        nudges = self.generator.evaluate_and_generate(hipotesis)

        self.assertTrue(len(nudges) >= 1)
        # Debe haber un nudge solicitando Business Owner
        bo_nudge = next((n for n in nudges if "Dueño de Negocio" in n.question_title), None)
        self.assertIsNotNone(bo_nudge)
        self.assertIn("AdaptiveCard", bo_nudge.payload.get("type", ""))
        self.assertTrue(len(bo_nudge.quick_actions) >= 1)

    def test_generates_nudge_for_low_confidence(self):
        hipotesis = HipotesisFactSheet(
            entity_name="Sistema Dudoso",
            candidate_type="Application",
            technical_stack="Java 17",
            provider="Proveedor X",
            sla_uptime="99.0%",
            confidence_score=0.72,  # Debajo del umbral 0.85
            status="Requires_Verification",
            business_owner="Gerente Operaciones",
            technical_owner="Dev <dev@test.com>",
        )
        nudges = self.generator.evaluate_and_generate(hipotesis)

        conf_nudge = next((n for n in nudges if "Correlación" in n.question_title), None)
        self.assertIsNotNone(conf_nudge)
        self.assertIn("Correlación", conf_nudge.question_title)
        self.assertTrue(any(a["action"] == "approve_correlation" for a in conf_nudge.quick_actions))


class TestEndToEndPipeline(unittest.TestCase):
    """Prueba de integración de punta a punta del script run_discovery."""

    def test_full_pipeline_execution(self):
        output = run_discovery.run_pipeline()

        self.assertIn("fact_sheets", output)
        self.assertIn("nudges", output)
        # Solo la aplicación del catálogo con evidencia vinculada produce hipótesis;
        # el portal sin coincidencia en el catálogo queda como candidato huérfano.
        self.assertEqual([fs.catalog_id for fs in output["fact_sheets"]], ["APP-001"])
        self.assertTrue(len(output["orphans"]) >= 1)
        self.assertTrue(len(output["nudges"]) >= 2)

        # Verificar que el archivo JSON fue generado y contiene datos válidos
        output_path = Path(output["output_file"])
        self.assertTrue(output_path.is_file())

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(len(data["hypotheses"]), 1)
        hypothesis = data["hypotheses"][0]
        self.assertIn("fact_sheet", hypothesis)
        self.assertIn("technical_evidence", hypothesis)
        self.assertIn("contractual_evidence", hypothesis)
        self.assertIn("micro_nudges", hypothesis)
        self.assertTrue(len(data["orphan_candidates"]) >= 1)

if __name__ == "__main__":
    unittest.main()
