"""
Pruebas del evaluador del pipeline sobre el conjunto sintético etiquetado (evaluate.py).

Cubre:
- Cálculo de precisión, recall, F1, macro/micro promedio y matriz de confusión.
- Mapeo de resultados del pipeline a predicciones por evidencia, con precedencia.
- Exactitud del conjunto de app_ids y errores asociados.
- Integración con el conjunto sintético real y determinismo del reporte JSON.
"""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

MVP_DIR = Path(__file__).resolve().parent.parent
if str(MVP_DIR) not in sys.path:
    sys.path.insert(0, str(MVP_DIR))

import evaluate


def _item(evidence_id, outcome, app_ids):
    """Construye una etiqueta mínima con la forma de labels.json."""
    return {
        "evidence_id": evidence_id,
        "expected_outcome": outcome,
        "expected_app_ids": list(app_ids),
    }


def _pred(outcome, app_ids):
    """Construye una predicción mínima con la forma que produce el evaluador."""
    return {"outcome": outcome, "app_ids": list(app_ids)}


def _all_keys(value):
    """Recorre un reporte y devuelve todas las claves de sus diccionarios."""
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


_SYNTHETIC_BUNDLE = {}


def _synthetic_bundle():
    """
    Ejecuta el pipeline real una sola vez y reutiliza el reporte entre clases.

    El pipeline se ejecuta con `_run_and_predict`; luego se parchea esa función
    para que `evaluate_dataset` construya el reporte con las mismas predicciones
    sin volver a correr el corpus.
    """
    if _SYNTHETIC_BUNDLE:
        return _SYNTHETIC_BUNDLE

    dataset = MVP_DIR / "datasets" / "sintetico"
    labels = json.loads((dataset / "labels.json").read_text(encoding="utf-8"))
    predictions, multi_claim = evaluate._run_and_predict(
        dataset,
        evaluate.config.MIN_LINK_SCORE,
        evaluate.config.AMBIGUITY_MARGIN,
        evaluate.config.REVIEW_THRESHOLD,
        False,
    )
    with patch.object(
        evaluate, "_run_and_predict", return_value=(predictions, multi_claim)
    ):
        report = evaluate.evaluate_dataset(dataset, split="both")

    _SYNTHETIC_BUNDLE.update({
        "dataset": dataset,
        "labels": labels,
        "predictions": predictions,
        "multi_claim": multi_claim,
        "report": report,
    })
    return _SYNTHETIC_BUNDLE


class TestComputeMetrics(unittest.TestCase):
    """Pruebas del cálculo de métricas por clase y agregadas."""

    def test_perfect_predictions_score_one(self):
        labels = [
            _item("a", "linked", ["APP-001"]),
            _item("b", "orphan", []),
            _item("c", "conflict", ["APP-002", "APP-003"]),
            _item("d", "multi_app", ["APP-004", "APP-005"]),
        ]
        predictions = {
            "a": _pred("linked", ["APP-001"]),
            "b": _pred("orphan", []),
            "c": _pred("conflict", ["APP-002", "APP-003"]),
            "d": _pred("multi_app", ["APP-004", "APP-005"]),
        }

        result = evaluate.compute_metrics(labels, predictions)
        metrics = result["metrics"]

        self.assertEqual(result["n"], 4)
        for outcome in evaluate.OUTCOMES:
            with self.subTest(outcome=outcome):
                self.assertEqual(metrics["per_class"][outcome]["precision"], 1.0)
                self.assertEqual(metrics["per_class"][outcome]["recall"], 1.0)
                self.assertEqual(metrics["per_class"][outcome]["f1"], 1.0)
        self.assertEqual(metrics["macro"]["precision"], 1.0)
        self.assertEqual(metrics["macro"]["recall"], 1.0)
        self.assertEqual(metrics["macro"]["f1"], 1.0)
        self.assertEqual(metrics["micro"]["accuracy"], 1.0)
        self.assertEqual(metrics["micro"]["precision"], 1.0)
        self.assertEqual(metrics["micro"]["recall"], 1.0)
        self.assertEqual(metrics["micro"]["f1"], 1.0)
        self.assertEqual(metrics["app_id_accuracy"]["evaluated"], 2)
        self.assertEqual(metrics["app_id_accuracy"]["correct"], 2)
        self.assertEqual(metrics["app_id_accuracy"]["accuracy"], 1.0)

    def test_one_false_negative_and_one_false_positive(self):
        labels = [
            _item("e1", "linked", ["APP-001"]),
            _item("e2", "linked", ["APP-002"]),
            _item("e3", "orphan", []),
        ]
        predictions = {
            "e1": _pred("linked", ["APP-001"]),
            "e2": _pred("orphan", []),
            "e3": _pred("orphan", []),
        }

        metrics = evaluate.compute_metrics(labels, predictions)["metrics"]

        linked = metrics["per_class"]["linked"]
        self.assertEqual(linked["support"], 2)
        self.assertEqual(linked["precision"], 1.0)
        self.assertEqual(linked["recall"], 0.5)
        self.assertAlmostEqual(linked["f1"], 0.6667, places=4)

        orphan = metrics["per_class"]["orphan"]
        self.assertEqual(orphan["support"], 1)
        self.assertEqual(orphan["precision"], 0.5)
        self.assertEqual(orphan["recall"], 1.0)
        self.assertAlmostEqual(orphan["f1"], 0.6667, places=4)

        self.assertEqual(metrics["per_class"]["conflict"]["support"], 0)
        self.assertEqual(metrics["per_class"]["conflict"]["precision"], 0.0)
        self.assertEqual(metrics["per_class"]["multi_app"]["recall"], 0.0)

        self.assertAlmostEqual(metrics["macro"]["precision"], 0.375, places=4)
        self.assertAlmostEqual(metrics["macro"]["recall"], 0.375, places=4)
        self.assertAlmostEqual(metrics["macro"]["f1"], 0.3333, places=4)

        self.assertAlmostEqual(metrics["micro"]["accuracy"], 0.6667, places=4)
        self.assertAlmostEqual(metrics["micro"]["precision"], 0.6667, places=4)
        self.assertAlmostEqual(metrics["micro"]["recall"], 0.6667, places=4)
        self.assertAlmostEqual(metrics["micro"]["f1"], 0.6667, places=4)

    def test_confusion_matrix_orientation_is_expected_rows_by_predicted_columns(self):
        labels = [_item("asimetrico", "linked", ["APP-001"])]
        predictions = {"asimetrico": _pred("orphan", [])}

        result = evaluate.compute_metrics(labels, predictions)
        rows = result["confusion_matrix"]["rows"]

        # La única celda debe estar en (esperado=linked, predicho=orphan).
        self.assertEqual(rows["linked"]["orphan"], 1)
        self.assertEqual(rows["orphan"]["linked"], 0)
        self.assertEqual(rows["linked"]["linked"], 0)
        self.assertEqual(rows["orphan"]["orphan"], 0)
        self.assertEqual(rows["linked"]["missing"], 0)
        self.assertEqual(result["metrics"]["per_class"]["linked"]["recall"], 0.0)
        self.assertEqual(result["metrics"]["per_class"]["orphan"]["precision"], 0.0)

    def test_missing_prediction_lands_in_missing_column_and_lowers_recall(self):
        labels = [
            _item("presente", "linked", ["APP-001"]),
            _item("ausente", "linked", ["APP-002"]),
            _item("huerfano", "orphan", []),
        ]
        predictions = {
            "presente": _pred("linked", ["APP-001"]),
            "huerfano": _pred("orphan", []),
        }

        result = evaluate.compute_metrics(labels, predictions)
        rows = result["confusion_matrix"]["rows"]
        metrics = result["metrics"]

        # La evidencia sin predicción va a la pseudo-columna `missing`, no a `orphan`.
        self.assertEqual(rows["linked"]["missing"], 1)
        self.assertEqual(rows["linked"]["linked"], 1)
        self.assertEqual(rows["linked"]["orphan"], 0)
        self.assertEqual(sum(rows["linked"].values()), 2)

        linked = metrics["per_class"]["linked"]
        self.assertEqual(linked["support"], 2)
        self.assertEqual(linked["precision"], 1.0)
        self.assertEqual(linked["recall"], 0.5)
        self.assertAlmostEqual(linked["f1"], 0.6667, places=4)
        self.assertAlmostEqual(metrics["micro"]["accuracy"], 0.6667, places=4)

    def test_empty_split_does_not_divide_by_zero(self):
        result = evaluate.compute_metrics([], {})

        self.assertEqual(result["n"], 0)
        self.assertEqual(result["metrics"]["macro"]["precision"], 0.0)
        self.assertEqual(result["metrics"]["macro"]["recall"], 0.0)
        self.assertEqual(result["metrics"]["macro"]["f1"], 0.0)
        self.assertEqual(result["metrics"]["micro"]["precision"], 0.0)
        self.assertEqual(result["metrics"]["micro"]["recall"], 0.0)
        self.assertEqual(result["metrics"]["micro"]["f1"], 0.0)
        self.assertEqual(result["metrics"]["micro"]["accuracy"], 0.0)
        self.assertEqual(result["metrics"]["app_id_accuracy"]["evaluated"], 0)
        self.assertIsNone(result["metrics"]["app_id_accuracy"]["accuracy"])
        for outcome in evaluate.OUTCOMES:
            with self.subTest(outcome=outcome):
                self.assertEqual(result["metrics"]["per_class"][outcome]["support"], 0)
                self.assertEqual(result["metrics"]["per_class"][outcome]["f1"], 0.0)
                self.assertEqual(sum(result["confusion_matrix"]["rows"][outcome].values()), 0)


class TestPredictionsFromRun(unittest.TestCase):
    """Pruebas del mapeo de la salida del pipeline a predicciones por evidencia."""

    def test_precedence_between_outcomes(self):
        run = {
            "fact_sheets": [
                SimpleNamespace(
                    catalog_id="APP-001",
                    confidence_score=0.90,
                    linked_repos=["repo-a", "repo-x", "repo-compartido"],
                    linked_contracts=["TDR-001"],
                    multi_application_contracts={"TDR-001": ["APP-001", "APP-002"]},
                ),
                SimpleNamespace(
                    catalog_id="APP-002",
                    confidence_score=0.80,
                    linked_repos=[],
                    linked_contracts=["TDR-001"],
                    multi_application_contracts={"TDR-001": ["APP-001", "APP-002"]},
                ),
                SimpleNamespace(
                    catalog_id="APP-003",
                    confidence_score=0.50,
                    linked_repos=["repo-compartido"],
                    linked_contracts=[],
                    multi_application_contracts={},
                ),
            ],
            "conflicts": [
                SimpleNamespace(
                    name="repo-x",
                    candidates=[{"catalog_id": "APP-004"}, {"catalog_id": "APP-005"}],
                ),
            ],
            "orphans": [SimpleNamespace(name="repo-huerfano")],
        }

        predictions, multi_claim = evaluate.predictions_from_run(run)

        # Un contrato en linked_contracts y en multi_application_contracts es multi_aplicación.
        self.assertEqual(predictions["TDR-001"]["outcome"], "multi_app")
        self.assertEqual(predictions["TDR-001"]["app_ids"], ["APP-001", "APP-002"])

        # Un repositorio en conflictos es conflicto aunque también aparezca vinculado.
        self.assertEqual(predictions["repo-x"]["outcome"], "conflict")
        self.assertEqual(predictions["repo-x"]["app_ids"], ["APP-004", "APP-005"])

        # Un huérfano se reporta como tal, sin app_ids.
        self.assertEqual(predictions["repo-huerfano"]["outcome"], "orphan")
        self.assertEqual(predictions["repo-huerfano"]["app_ids"], [])

        # Un vínculo normal se reporta como linked con la app anclada.
        self.assertEqual(predictions["repo-a"]["outcome"], "linked")
        self.assertEqual(predictions["repo-a"]["app_ids"], ["APP-001"])

        # La evidencia reclamada por dos hipótesis usa la de mayor confianza y se registra.
        self.assertEqual(predictions["repo-compartido"]["outcome"], "linked")
        self.assertEqual(predictions["repo-compartido"]["app_ids"], ["APP-001"])
        self.assertEqual([e["evidence_id"] for e in multi_claim], ["repo-compartido"])

        # La evidencia que no aparece en la corrida queda sin predicción.
        self.assertNotIn("evidencia-ausente", predictions)


class TestAppIdAccuracy(unittest.TestCase):
    """Pruebas de la exactitud del conjunto de app_ids."""

    def test_correct_sets_pass_and_wrong_sets_are_listed(self):
        labels = [
            _item("ok-unico", "linked", ["APP-001"]),
            _item("ok-multi", "multi_app", ["APP-002", "APP-003"]),
            _item("mal-conjunto", "linked", ["APP-004"]),
            _item("mal-parcial", "multi_app", ["APP-006", "APP-007"]),
            _item("mal-outcome", "linked", ["APP-008"]),
        ]
        predictions = {
            "ok-unico": _pred("linked", ["APP-001"]),
            "ok-multi": _pred("multi_app", ["APP-003", "APP-002"]),
            "mal-conjunto": _pred("linked", ["APP-004", "APP-005"]),
            "mal-parcial": _pred("multi_app", ["APP-006"]),
            "mal-outcome": _pred("orphan", []),
        }

        result = evaluate.compute_metrics(labels, predictions)
        accuracy = result["metrics"]["app_id_accuracy"]

        self.assertEqual(accuracy["evaluated"], 4)
        self.assertEqual(accuracy["correct"], 2)
        self.assertEqual(accuracy["accuracy"], 0.5)

        mismatches = result["app_id_mismatches"]
        self.assertEqual(
            [e["evidence_id"] for e in mismatches],
            ["mal-conjunto", "mal-parcial"],
        )
        self.assertEqual(mismatches[0]["expected_app_ids"], ["APP-004"])
        self.assertEqual(mismatches[0]["predicted_app_ids"], ["APP-004", "APP-005"])
        self.assertEqual(mismatches[1]["expected_app_ids"], ["APP-006", "APP-007"])
        self.assertEqual(mismatches[1]["predicted_app_ids"], ["APP-006"])


class TestEvaluationErrors(unittest.TestCase):
    """Pruebas de la separación entre evidencia sin predicción y predicción sin etiqueta."""

    def _build_dataset(self, root):
        """Crea un conjunto mínimo válido para evaluar sin correr el pipeline real."""
        (root / "repos").mkdir()
        (root / "contratos").mkdir()
        (root / "catalogo_aplicaciones.csv").write_text(
            "codigo,nombre\nAPP-001,Uno\n", encoding="utf-8"
        )
        labels = {
            "items": [
                {
                    "evidence_id": "sin-prediccion",
                    "expected_outcome": "linked",
                    "expected_app_ids": ["APP-001"],
                    "split": "evaluation",
                },
                {
                    "evidence_id": "con-prediccion",
                    "expected_outcome": "orphan",
                    "expected_app_ids": [],
                    "split": "calibration",
                },
            ]
        }
        (root / "labels.json").write_text(
            json.dumps(labels, ensure_ascii=False), encoding="utf-8"
        )

    def test_missing_and_unlabeled_predictions_are_not_swapped(self):
        predictions = {
            "con-prediccion": _pred("orphan", []),
            "prediccion-sin-etiqueta": _pred("linked", ["APP-001"]),
        }

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._build_dataset(root)
            with patch.object(
                evaluate, "_run_and_predict", return_value=(predictions, [])
            ):
                report = evaluate.evaluate_dataset(root, split="all")

        errors = report["errors"]
        self.assertEqual(errors["missing_predictions"], ["sin-prediccion"])
        self.assertEqual(errors["unlabeled_predictions"], ["prediccion-sin-etiqueta"])
        self.assertIn("sin-prediccion", errors["missing_predictions"])
        self.assertNotIn("prediccion-sin-etiqueta", errors["missing_predictions"])
        self.assertIn("prediccion-sin-etiqueta", errors["unlabeled_predictions"])
        self.assertNotIn("sin-prediccion", errors["unlabeled_predictions"])

        # La evidencia sin predicción también debe caer en la columna `missing`.
        rows = report["splits"]["all"]["confusion_matrix"]["rows"]
        self.assertEqual(rows["linked"]["missing"], 1)
        self.assertEqual(rows["linked"]["linked"], 0)


class TestCliSurface(unittest.TestCase):
    """Pruebas de la interfaz de línea de comandos y sus parámetros."""

    @classmethod
    def setUpClass(cls):
        bundle = _synthetic_bundle()
        cls.predictions = bundle["predictions"]
        cls.multi_claim = bundle["multi_claim"]

    def _run_main(self, argv):
        """Ejecuta `main` con las predicciones reales ya calculadas."""
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(
            evaluate, "_run_and_predict", return_value=(self.predictions, self.multi_claim)
        ), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = evaluate.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_default_dataset_returns_zero_and_writes_valid_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "reporte.json"
            code, stdout, stderr = self._run_main(["--json", str(report_path)])

            self.assertEqual(code, 0, stderr)
            self.assertIn("EVALUACIÓN DEL PIPELINE DE DESCUBRIMIENTO", stdout)
            self.assertIn("corpus es sintético", stdout)
            self.assertTrue(report_path.is_file())

            data = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema"], "mvp.evaluation.v1")
            self.assertEqual(data["dataset"], "datasets/sintetico")

    def test_nonexistent_dataset_returns_non_zero_with_readable_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "no-debe-escribirse.json"
            missing = MVP_DIR / "datasets" / "no-existe"
            code, _, stderr = self._run_main(
                ["--dataset", str(missing), "--json", str(report_path)]
            )

            self.assertNotEqual(code, 0)
            self.assertIn("No se encontró el conjunto de datos", stderr)
            self.assertFalse(report_path.exists())

    def test_evaluation_split_and_threshold_overrides_reach_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "evaluacion.json"
            code, stdout, stderr = self._run_main([
                "--split", "evaluation",
                "--min-link-score", "0.42",
                "--ambiguity-margin", "0.07",
                "--review-threshold", "0.91",
                "--json", str(report_path),
            ])

            self.assertEqual(code, 0, stderr)
            data = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(list(data["splits"]), ["evaluation"])
            self.assertEqual(
                data["params"],
                {
                    "min_link_score": 0.42,
                    "ambiguity_margin": 0.07,
                    "review_threshold": 0.91,
                },
            )
            self.assertNotIn("Partición: calibration", stdout)


class TestSyntheticDatasetEvaluation(unittest.TestCase):
    """Integración con el conjunto sintético real (una sola corrida del pipeline)."""

    @classmethod
    def setUpClass(cls):
        bundle = _synthetic_bundle()
        cls.dataset = bundle["dataset"]
        cls.labels = bundle["labels"]
        cls.predictions = bundle["predictions"]
        cls.report = bundle["report"]

    def test_schema_and_written_report_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = evaluate.write_report(self.report, Path(tmp) / "reporte.json")
            data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(set(data), {"schema", "dataset", "params", "splits", "errors"})
        self.assertEqual(data["schema"], "mvp.evaluation.v1")
        self.assertEqual(data["dataset"], "datasets/sintetico")
        self.assertEqual(
            set(data["params"]),
            {"min_link_score", "ambiguity_margin", "review_threshold"},
        )
        self.assertEqual(set(data["splits"]), {"evaluation", "calibration", "all"})

        for name, split in data["splits"].items():
            with self.subTest(split=name):
                self.assertEqual(set(split), {"n", "metrics", "confusion_matrix"})
                self.assertEqual(
                    set(split["metrics"]),
                    {"per_class", "macro", "micro", "app_id_accuracy"},
                )
                self.assertEqual(set(split["metrics"]["per_class"]), set(evaluate.OUTCOMES))
                self.assertEqual(set(split["metrics"]["macro"]), {"precision", "recall", "f1"})
                self.assertEqual(
                    set(split["metrics"]["micro"]),
                    {"precision", "recall", "f1", "accuracy"},
                )
                matrix = split["confusion_matrix"]
                self.assertEqual(set(matrix), {"classes", "columns", "rows"})
                self.assertEqual(matrix["columns"], list(evaluate.COLUMNS))
                self.assertEqual(set(matrix["rows"]), set(evaluate.OUTCOMES))
                for row in matrix["rows"].values():
                    self.assertEqual(set(row), set(evaluate.COLUMNS))

        self.assertEqual(
            set(data["errors"]),
            {"missing_predictions", "unlabeled_predictions", "app_id_mismatches", "multi_claim"},
        )

        text = evaluate.format_text_report(data)
        self.assertIn("corpus es sintético", text)
        self.assertIn("no el desempeño en una organización real", text)

    def test_report_is_byte_identical_and_has_no_timestamp_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = evaluate.write_report(self.report, Path(tmp) / "uno.json")
            second = evaluate.write_report(self.report, Path(tmp) / "dos.json")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            payload = first.read_text(encoding="utf-8").lower()

        forbidden = {
            "timestamp", "generated_at", "created_at", "updated_at",
            "evaluated_at", "date", "time",
        }
        found = [
            key for key in _all_keys(self.report)
            if key.lower() in forbidden or key.lower().endswith("_at")
        ]
        self.assertEqual(found, [])
        self.assertNotIn("timestamp", payload)

    def test_every_labeled_item_gets_a_prediction(self):
        self.assertEqual(self.report["errors"]["missing_predictions"], [])
        self.assertEqual(len(self.report["errors"]["missing_predictions"]), 0)

    def test_confusion_matrix_totals_match_label_counts(self):
        counts = {"evaluation": 0, "calibration": 0, "all": 0}
        for item in self.labels["items"]:
            counts["all"] += 1
            counts[item["split"]] += 1
        expected = {"evaluation": 10, "calibration": 26, "all": 36}
        self.assertEqual(counts, expected)
        for split, total in expected.items():
            with self.subTest(split=split):
                matrix = self.report["splits"][split]["confusion_matrix"]["rows"]
                observed = sum(sum(row.values()) for row in matrix.values())
                self.assertEqual(observed, total)
                self.assertEqual(self.report["splits"][split]["n"], total)


if __name__ == "__main__":
    unittest.main()
