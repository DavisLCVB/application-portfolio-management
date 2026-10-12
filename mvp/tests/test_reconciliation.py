"""
Pruebas de la reconciliación N:M del Agente 3.

Cubre:
- Vinculación N:M entre evidencias técnicas y contractuales con score mínimo.
- "Sin coincidencia" como resultado válido (candidato huérfano).
- Anclaje en el catálogo existente como identidad de la aplicación.
"""

import dataclasses
import sys
import unittest
from pathlib import Path

MVP_DIR = Path(__file__).resolve().parent.parent
if str(MVP_DIR) not in sys.path:
    sys.path.insert(0, str(MVP_DIR))

from src import config
from src.code_to_catalog import CodeToCatalogExtractor
from src.contract_miner import ContractMiner
from src.models import AplicacionCatalogo, CandidatoHuerfano, ResultadoReconciliacion
from src.reconciliator import SemanticReconciliator, load_catalog
import run_discovery

FIXTURES_DIR = MVP_DIR / "fixtures"
CATALOG_CSV = FIXTURES_DIR / "catalogs" / "catalogo_aplicaciones.csv"


class TestNToMReconciliation(unittest.TestCase):
    """El reconciliador vincula N:M y nunca fuerza una coincidencia."""

    @classmethod
    def setUpClass(cls):
        extractor = CodeToCatalogExtractor()
        miner = ContractMiner()
        cls.tech_recaudacion = extractor.extract(str(FIXTURES_DIR / "repo-recaudacion"))
        cls.tech_portal = extractor.extract(str(FIXTURES_DIR / "repo-portal-atencion"))
        cls.contract_recaudacion = miner.extract(str(FIXTURES_DIR / "contracts" / "tdr-recaudacion-digital.md"))
        cls.contract_portal = miner.extract(str(FIXTURES_DIR / "contracts" / "tdr-portal-ciudadano.md"))
        # Repositorio adicional del mismo sistema (N:M: un contrato cubre varios repos)
        cls.tech_recaudacion_batch = dataclasses.replace(
            cls.tech_recaudacion, repo_name="recaudacion-digital-batch"
        )
        # Repositorio sin relación con ningún contrato (posible Shadow IT)
        cls.tech_unrelated = dataclasses.replace(
            cls.tech_recaudacion,
            repo_name="inventario-bodega-almacen",
            primary_language="Python",
            runtime_version="Python 3.12",
            dependencies=["django", "celery"],
            endpoints=["GET /api/bodega/stock"],
        )

    def setUp(self):
        self.reconciliator = SemanticReconciliator()

    def _linked_pairs(self, result):
        return {(tech.repo_name, contract.doc_id) for _, tech, contract in result.links}

    def test_match_all_returns_reconciliation_result(self):
        result = self.reconciliator.match_all([self.tech_recaudacion], [self.contract_recaudacion])
        self.assertIsInstance(result, ResultadoReconciliacion)

    def test_unrelated_repo_is_orphan_not_forced(self):
        result = self.reconciliator.match_all(
            [self.tech_recaudacion, self.tech_portal, self.tech_unrelated],
            [self.contract_recaudacion, self.contract_portal],
        )
        linked_repos = {repo for repo, _ in self._linked_pairs(result)}
        self.assertNotIn("inventario-bodega-almacen", linked_repos)

        orphan_names = {o.name for o in result.orphans}
        self.assertIn("inventario-bodega-almacen", orphan_names)
        orphan = next(o for o in result.orphans if o.name == "inventario-bodega-almacen")
        self.assertIsInstance(orphan, CandidatoHuerfano)
        self.assertEqual(orphan.evidence_type, "repositorio")
        self.assertLess(orphan.best_score, self.reconciliator.min_link_score)
        self.assertTrue(len(orphan.primary_citations) > 0)

    def test_contract_without_repo_is_orphan(self):
        result = self.reconciliator.match_all(
            [self.tech_recaudacion],
            [self.contract_recaudacion, self.contract_portal],
        )
        self.assertEqual(self._linked_pairs(result), {("recaudacion-digital-service", "TDR-2024-MEF-0089")})
        orphan = next(o for o in result.orphans if o.name == "TDR-2023-MEF-0145")
        self.assertEqual(orphan.evidence_type, "contrato")

    def test_one_contract_links_to_several_repos(self):
        result = self.reconciliator.match_all(
            [self.tech_recaudacion, self.tech_recaudacion_batch, self.tech_portal],
            [self.contract_recaudacion, self.contract_portal],
        )
        pairs = self._linked_pairs(result)
        self.assertIn(("recaudacion-digital-service", "TDR-2024-MEF-0089"), pairs)
        self.assertIn(("recaudacion-digital-batch", "TDR-2024-MEF-0089"), pairs)
        self.assertIn(("portal-atencion-ciudadano", "TDR-2023-MEF-0145"), pairs)
        self.assertEqual(result.orphans, [])

    def test_one_repo_links_to_several_contracts(self):
        reconciliator = SemanticReconciliator(min_link_score=0.0)
        result = reconciliator.match_all(
            [self.tech_recaudacion],
            [self.contract_recaudacion, self.contract_portal],
        )
        self.assertEqual(len(result.links), 2)

    def test_min_link_score_is_configurable_and_below_review_threshold(self):
        self.assertEqual(self.reconciliator.min_link_score, config.MIN_LINK_SCORE)
        self.assertLess(config.MIN_LINK_SCORE, self.reconciliator.confidence_threshold)
        strict = SemanticReconciliator(min_link_score=0.99)
        result = strict.match_all([self.tech_recaudacion], [self.contract_recaudacion])
        self.assertEqual(result.links, [])
        self.assertEqual(len(result.orphans), 2)


class TestCatalogAnchoring(unittest.TestCase):
    """El catálogo existente es el ancla de identidad de las hipótesis."""

    @classmethod
    def setUpClass(cls):
        extractor = CodeToCatalogExtractor()
        miner = ContractMiner()
        cls.catalog = load_catalog(CATALOG_CSV)
        cls.tech_recaudacion = extractor.extract(str(FIXTURES_DIR / "repo-recaudacion"))
        cls.tech_portal = extractor.extract(str(FIXTURES_DIR / "repo-portal-atencion"))
        cls.contract_recaudacion = miner.extract(str(FIXTURES_DIR / "contracts" / "tdr-recaudacion-digital.md"))
        cls.contract_portal = miner.extract(str(FIXTURES_DIR / "contracts" / "tdr-portal-ciudadano.md"))
        cls.tech_recaudacion_batch = dataclasses.replace(
            cls.tech_recaudacion, repo_name="recaudacion-digital-batch"
        )

    def setUp(self):
        self.reconciliator = SemanticReconciliator()

    def test_load_catalog_reads_identity_and_aliases(self):
        self.assertEqual(len(self.catalog), 3)
        app = self.catalog[0]
        self.assertIsInstance(app, AplicacionCatalogo)
        self.assertEqual(app.code, "APP-001")
        self.assertEqual(app.name, "Sistema Integrado de Tesorería")
        self.assertIn("Recaudación Digital", app.aliases)
        self.assertIn("cmendoza@mef.gob.pe", app.technical_owner)
        self.assertIn("catalogo_aplicaciones.csv#R2", app.citation)

    def test_evidence_is_anchored_to_catalog_application(self):
        result = self.reconciliator.reconcile_with_catalog(
            self.catalog,
            [self.tech_recaudacion, self.tech_portal],
            [self.contract_recaudacion, self.contract_portal],
        )
        self.assertEqual(len(result.hypotheses), 1)
        anchored = result.hypotheses[0]
        fs = anchored.fact_sheet
        self.assertEqual(fs.catalog_id, "APP-001")
        self.assertEqual(fs.entity_name, "Sistema Integrado de Tesorería")
        self.assertEqual(fs.linked_repos, ["recaudacion-digital-service"])
        self.assertEqual(fs.linked_contracts, ["TDR-2024-MEF-0089"])
        self.assertTrue(any(c["source"] == "existing_catalog" for c in fs.primary_citations))

    def test_evidence_without_catalog_match_is_orphan(self):
        result = self.reconciliator.reconcile_with_catalog(
            self.catalog,
            [self.tech_recaudacion, self.tech_portal],
            [self.contract_recaudacion, self.contract_portal],
        )
        orphans = {o.name: o for o in result.orphans}
        self.assertEqual(set(orphans), {"portal-atencion-ciudadano", "TDR-2023-MEF-0145"})
        # Los huérfanos que se vinculan entre sí se reportan juntos para la revisión humana
        self.assertIn("TDR-2023-MEF-0145", orphans["portal-atencion-ciudadano"].related)
        self.assertIn("portal-atencion-ciudadano", orphans["TDR-2023-MEF-0145"].related)

    def test_catalog_application_links_several_repos(self):
        result = self.reconciliator.reconcile_with_catalog(
            self.catalog,
            [self.tech_recaudacion, self.tech_recaudacion_batch],
            [self.contract_recaudacion],
        )
        fs = result.hypotheses[0].fact_sheet
        self.assertEqual(sorted(fs.linked_repos), ["recaudacion-digital-batch", "recaudacion-digital-service"])
        self.assertEqual(result.orphans, [])

    def test_empty_catalog_makes_every_evidence_orphan(self):
        result = self.reconciliator.reconcile_with_catalog(
            [], [self.tech_recaudacion], [self.contract_recaudacion]
        )
        self.assertEqual(result.hypotheses, [])
        self.assertEqual(len(result.orphans), 2)

    def test_pipeline_reports_anchored_hypotheses_and_orphans(self):
        output = run_discovery.run_pipeline(scan_dir=FIXTURES_DIR)
        self.assertEqual([fs.catalog_id for fs in output["fact_sheets"]], ["APP-001"])
        orphan_names = {o.name for o in output["orphans"]}
        self.assertIn("portal-atencion-ciudadano", orphan_names)
        # Las filas del catálogo no deben tratarse como evidencia técnica huérfana
        self.assertNotIn("Ventanilla Única de Trámites", orphan_names)


if __name__ == "__main__":
    unittest.main()
