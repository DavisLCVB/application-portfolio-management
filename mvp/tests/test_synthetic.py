"""
Pruebas del generador determinista del conjunto sintético etiquetado (src/synthetic.py).
"""

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

MVP_DIR = Path(__file__).resolve().parent.parent
if str(MVP_DIR) not in sys.path:
    sys.path.insert(0, str(MVP_DIR))

from src import synthetic
from src.code_to_catalog import CodeToCatalogExtractor
from src.contract_miner import ContractMiner
from src.reconciliator import load_catalog
import run_discovery


def _tree_hashes(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


class TestSyntheticDataset(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name) / "ds"
        synthetic.generate(seed=42, out_dir=cls.root)
        cls.labels = json.loads((cls.root / "labels.json").read_text(encoding="utf-8"))
        cls.catalog = load_catalog(cls.root / synthetic.CATALOG_FILE)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_same_seed_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "ds"
            synthetic.generate(seed=42, out_dir=other)
            self.assertEqual(_tree_hashes(self.root), _tree_hashes(other))

    def test_regenerating_in_place_is_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "ds"
            synthetic.generate(seed=7, out_dir=out)
            synthetic.generate(seed=42, out_dir=out)
            self.assertEqual(_tree_hashes(self.root), _tree_hashes(out))

    def test_refuses_non_dataset_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "unrelated.txt").write_text("x", encoding="utf-8")
            with self.assertRaises(ValueError):
                synthetic.generate(seed=42, out_dir=Path(tmp))

    def test_different_seed_changes_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "ds"
            synthetic.generate(seed=43, out_dir=other)
            self.assertNotEqual(_tree_hashes(self.root), _tree_hashes(other))

    def test_catalog_has_about_thirty_applications(self):
        self.assertGreaterEqual(len(self.catalog), 28)
        self.assertLessEqual(len(self.catalog), 32)
        self.assertEqual(len({a.code for a in self.catalog}), len(self.catalog))

    def test_every_category_present_with_minimum_count(self):
        counts = {}
        for item in self.labels["items"]:
            counts[item["category"]] = counts.get(item["category"], 0) + 1
        for category in synthetic.CATEGORIES:
            self.assertGreaterEqual(counts.get(category, 0), 4, category)
        self.assertEqual(counts, self.labels["category_counts"])

    def test_labels_reference_existing_apps_and_evidence(self):
        codes = {a.code for a in self.catalog}
        ids = [item["evidence_id"] for item in self.labels["items"]]
        self.assertEqual(len(ids), len(set(ids)))
        for item in self.labels["items"]:
            self.assertTrue((self.root / item["path"]).exists(), item["path"])
            self.assertTrue(set(item["expected_app_ids"]) <= codes, item)
            n = len(item["expected_app_ids"])
            expected_n = {"linked": n == 1, "orphan": n == 0, "conflict": n >= 2, "multi_app": n >= 2}
            self.assertTrue(expected_n[item["expected_outcome"]], item)

    def test_split_is_stratified_and_near_seventy_thirty(self):
        items = self.labels["items"]
        cal = [i for i in items if i["split"] == "calibration"]
        self.assertTrue(all(i["split"] in ("calibration", "evaluation") for i in items))
        self.assertAlmostEqual(len(cal) / len(items), 0.7, delta=0.08)
        for category in synthetic.CATEGORIES:
            in_cat = [i for i in items if i["category"] == category]
            self.assertTrue(any(i["split"] == "evaluation" for i in in_cat), category)
            self.assertTrue(any(i["split"] == "calibration" for i in in_cat), category)

    def test_evidence_parses_with_existing_agents(self):
        extractor, miner = CodeToCatalogExtractor(), ContractMiner()
        for item in self.labels["items"]:
            path = self.root / item["path"]
            if item["evidence_type"] == "repositorio":
                self.assertEqual(extractor.extract(str(path)).repo_name, item["evidence_id"])
            else:
                self.assertEqual(miner.extract(str(path)).doc_id, item["evidence_id"])

    def test_pipeline_runs_end_to_end_on_dataset(self):
        with contextlib.redirect_stdout(io.StringIO()):
            output = run_discovery.run_pipeline(
                repos_dir=self.root / synthetic.REPOS_DIR,
                contracts_dir=self.root / synthetic.CONTRACTS_DIR,
                catalog_path=self.root / synthetic.CATALOG_FILE,
            )
        seen = {fs.catalog_id for fs in output["fact_sheets"]}
        self.assertTrue(seen)
        self.assertTrue(output["orphans"])


if __name__ == "__main__":
    unittest.main()
