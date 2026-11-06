"""
Pruebas del barrido de umbrales del reconciliador (calibrate.py).

Cubre:
- Selección de `MIN_LINK_SCORE` y `AMBIGUITY_MARGIN` por plateau y mediana.
- Desempates por F1 macro y por menor número de conflictos.
- Aislamiento de la partición de calibración (la evaluación nunca selecciona).
- Selección de `REVIEW_THRESHOLD` por tasa de error de lo auto-publicado.
- Exactitud de app_ids por conjunto exacto versus superconjunto.
- Determinismo del reporte JSON y humo sobre el corpus sintético real.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

MVP_DIR = Path(__file__).resolve().parent.parent
if str(MVP_DIR) not in sys.path:
    sys.path.insert(0, str(MVP_DIR))

import calibrate
import evaluate


def _row(min_link_score, ambiguity_margin, accuracy, macro_f1, conflicts=0):
    """Construye una fila de barrido con la forma que consume `select_params`."""
    return {
        "min_link_score": min_link_score,
        "ambiguity_margin": ambiguity_margin,
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "conflicts": conflicts,
    }


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


class TestSelectParams(unittest.TestCase):
    """Pruebas de la regla de selección sobre la partición de calibración."""

    def test_plateau_is_selected_by_median_not_by_edge(self):
        # Tres combinaciones empatan en exactitud, F1 macro y conflictos.
        # Ordenadas por (min_link_score, ambiguity_margin), la mediana es la
        # combinación central: (0.40, 0.10), nunca un extremo del plateau.
        rows = [
            _row(0.30, 0.01, 0.90, 0.85),
            _row(0.40, 0.10, 0.90, 0.85),
            _row(0.50, 0.05, 0.90, 0.85),
            _row(0.70, 0.20, 0.80, 0.70),
        ]

        selection = calibrate.select_params(rows)

        self.assertEqual(selection["plateau_size"], 3)
        self.assertEqual(selection["min_link_score"], 0.40)
        self.assertEqual(selection["ambiguity_margin"], 0.10)
        # Debe ser estrictamente interior al plateau, no el mínimo ni el máximo.
        self.assertNotEqual(
            (selection["min_link_score"], selection["ambiguity_margin"]), (0.30, 0.01)
        )
        self.assertNotEqual(
            (selection["min_link_score"], selection["ambiguity_margin"]), (0.50, 0.05)
        )

    def test_macro_f1_breaks_accuracy_tie_before_conflicts(self):
        rows = [
            _row(0.30, 0.01, 0.90, 0.70, conflicts=0),
            _row(0.40, 0.05, 0.90, 0.80, conflicts=3),
            _row(0.60, 0.05, 0.80, 0.95, conflicts=0),
        ]

        selection = calibrate.select_params(rows)

        self.assertEqual(selection["plateau_size"], 1)
        self.assertEqual(selection["min_link_score"], 0.40)
        self.assertEqual(selection["ambiguity_margin"], 0.05)
        self.assertEqual(selection["macro_f1"], 0.80)

    def test_fewer_conflicts_breaks_accuracy_and_f1_tie(self):
        rows = [
            _row(0.30, 0.01, 0.90, 0.80, conflicts=2),
            _row(0.40, 0.05, 0.90, 0.80, conflicts=0),
            _row(0.60, 0.10, 0.90, 0.80, conflicts=1),
        ]

        selection = calibrate.select_params(rows)

        self.assertEqual(selection["plateau_size"], 1)
        self.assertEqual(selection["min_link_score"], 0.40)
        self.assertEqual(selection["ambiguity_margin"], 0.05)
        self.assertEqual(selection["conflicts"], 0)

    def test_empty_rows_raise_readable_error(self):
        with self.assertRaises(ValueError):
            calibrate.select_params([])


class TestCalibrationIsolation(unittest.TestCase):
    """La partición de evaluación no participa de la selección."""

    def test_selection_uses_only_calibration_rows(self):
        # Estructura: se separan las particiones antes de seleccionar. Aunque la
        # partición de evaluación prefiera (0.70, 0.20), la selección debe salir
        # de las filas de calibración, donde gana (0.50, 0.05).
        items = [
            {"evidence_id": "cal-1", "split": "calibration"},
            {"evidence_id": "eva-1", "split": "evaluation"},
        ]
        calibration_items = calibrate.filter_items(items, "calibration")
        self.assertEqual([item["evidence_id"] for item in calibration_items], ["cal-1"])

        calibration_rows = [
            _row(0.50, 0.05, 0.90, 0.85),
            _row(0.70, 0.20, 0.80, 0.75),
        ]
        evaluation_rows = [
            _row(0.50, 0.05, 0.70, 0.65),
            _row(0.70, 0.20, 0.95, 0.90),
        ]

        selection = calibrate.select_params(calibration_rows)

        self.assertEqual(
            (selection["min_link_score"], selection["ambiguity_margin"]), (0.50, 0.05)
        )
        # La tabla de evaluación habría elegido otro combo; no se le pasa a
        # `select_params` ni se consulta desde él.
        evaluation_selection = calibrate.select_params(evaluation_rows)
        self.assertEqual(
            (evaluation_selection["min_link_score"], evaluation_selection["ambiguity_margin"]),
            (0.70, 0.20),
        )


class TestSelectReviewThreshold(unittest.TestCase):
    """Pruebas de la selección de `REVIEW_THRESHOLD` por carga de revisión."""

    def test_smallest_zero_error_threshold_wins(self):
        rows = [
            {"threshold": 0.60, "auto_published": 5, "wrong": 2, "error_rate": 0.4, "review_load": 1},
            {"threshold": 0.70, "auto_published": 4, "wrong": 0, "error_rate": 0.0, "review_load": 2},
            {"threshold": 0.80, "auto_published": 3, "wrong": 0, "error_rate": 0.0, "review_load": 3},
        ]

        selection = calibrate.select_review_threshold(rows)

        self.assertEqual(selection["threshold"], 0.70)
        self.assertEqual(selection["wrong"], 0)
        self.assertEqual(selection["review_load"], 2)

    def test_without_zero_error_minimises_errors_then_review_load(self):
        rows = [
            {"threshold": 0.60, "auto_published": 6, "wrong": 3, "error_rate": 0.5, "review_load": 1},
            {"threshold": 0.70, "auto_published": 4, "wrong": 1, "error_rate": 0.25, "review_load": 3},
            {"threshold": 0.80, "auto_published": 2, "wrong": 1, "error_rate": 0.5, "review_load": 5},
        ]

        selection = calibrate.select_review_threshold(rows)

        self.assertEqual(selection["threshold"], 0.70)
        self.assertEqual(selection["wrong"], 1)
        self.assertEqual(selection["review_load"], 3)

    def test_threshold_with_nothing_published_is_not_a_zero_error_winner(self):
        # Un umbral que no publica nada no es un trade-off útil: su tasa de
        # error es indefinida, no cero. Debe caer al criterio de respaldo.
        rows = [
            {"threshold": 0.70, "auto_published": 5, "wrong": 1, "error_rate": 0.2, "review_load": 3},
            {"threshold": 0.90, "auto_published": 0, "wrong": 0, "error_rate": None, "review_load": 8},
        ]

        selection = calibrate.select_review_threshold(rows)

        self.assertEqual(selection["threshold"], 0.70)
        self.assertFalse(selection["zero_error"])

    def test_empty_rows_raise_readable_error(self):
        with self.assertRaises(ValueError):
            calibrate.select_review_threshold([])


class TestAppIdCriteria(unittest.TestCase):
    """Exactitud de app_ids: conjunto exacto frente a superconjunto."""

    def test_superset_of_expected_passes_superset_and_fails_exact(self):
        items = [_item("e1", "linked", ["APP-001"])]
        predictions = {"e1": _pred("linked", ["APP-001", "APP-002"])}

        criteria = calibrate.app_id_criteria(items, predictions)

        self.assertEqual(criteria["exact"]["evaluated"], 1)
        self.assertEqual(criteria["exact"]["correct"], 0)
        self.assertEqual(criteria["exact"]["accuracy"], 0.0)
        self.assertEqual(criteria["superset"]["evaluated"], 1)
        self.assertEqual(criteria["superset"]["correct"], 1)
        self.assertEqual(criteria["superset"]["accuracy"], 1.0)
        self.assertEqual([d["evidence_id"] for d in criteria["differences"]], ["e1"])

    def test_missing_expected_app_fails_both_criteria(self):
        items = [_item("e1", "multi_app", ["APP-001", "APP-002"])]
        predictions = {"e1": _pred("multi_app", ["APP-001"])}

        criteria = calibrate.app_id_criteria(items, predictions)

        self.assertEqual(criteria["exact"]["correct"], 0)
        self.assertEqual(criteria["superset"]["correct"], 0)
        self.assertEqual(criteria["differences"], [])

    def test_exact_match_passes_both_and_wrong_outcome_is_not_evaluated(self):
        items = [
            _item("ok", "linked", ["APP-001"]),
            _item("otro-resultado", "linked", ["APP-002"]),
        ]
        predictions = {
            "ok": _pred("linked", ["APP-001"]),
            "otro-resultado": _pred("orphan", []),
        }

        criteria = calibrate.app_id_criteria(items, predictions)

        self.assertEqual(criteria["exact"]["evaluated"], 1)
        self.assertEqual(criteria["exact"]["correct"], 1)
        self.assertEqual(criteria["superset"]["correct"], 1)
        self.assertEqual(criteria["differences"], [])


_TINY_REPORT = {}


def _tiny_report():
    """Construye una vez un reporte con rejilla mínima sobre el corpus real."""
    if not _TINY_REPORT:
        _TINY_REPORT.update(
            calibrate.build_report(
                MVP_DIR / "datasets" / "sintetico",
                min_link_scores=[0.45, 0.55],
                ambiguity_margins=[0.05, 0.15],
                review_thresholds=[0.70, 0.90],
            )
        )
    return _TINY_REPORT


class TestBuildReport(unittest.TestCase):
    """Humo e integración del reporte de calibración."""

    def test_schema_grid_and_evaluation_sections(self):
        report = _tiny_report()

        self.assertEqual(report["schema"], "mvp.calibration.v1")
        self.assertEqual(len(report["calibration_rows"]), 4)
        self.assertEqual(len(report["evaluation_rows"]), 4)

        self.assertIn(report["selection"]["min_link_score"], [0.45, 0.55])
        self.assertIn(report["selection"]["ambiguity_margin"], [0.05, 0.15])
        self.assertGreaterEqual(report["selection"]["plateau_size"], 1)

        for name in ("selected", "current"):
            evaluation = report["evaluation"][name]
            self.assertEqual(evaluation["schema"], "mvp.evaluation.v1")
            self.assertIn("evaluation", evaluation["splits"])

        app_ids = report["evaluation"]["app_id_criteria"]
        for name in ("selected", "current"):
            self.assertIn("exact", app_ids[name])
            self.assertIn("superset", app_ids[name])
            self.assertIn("differences", app_ids[name])

        self.assertIn("selection", report["review_threshold"])
        self.assertEqual(len(report["review_threshold"]["rows"]), 2)

    def test_two_builds_produce_byte_identical_json(self):
        kwargs = dict(
            min_link_scores=[0.45, 0.55],
            ambiguity_margins=[0.05, 0.15],
            review_thresholds=[0.70, 0.90],
        )
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "primero.json"
            second = Path(tmp) / "segundo.json"
            evaluate.write_report(
                calibrate.build_report(MVP_DIR / "datasets" / "sintetico", **kwargs), first
            )
            evaluate.write_report(
                calibrate.build_report(MVP_DIR / "datasets" / "sintetico", **kwargs), second
            )
            self.assertEqual(first.read_bytes(), second.read_bytes())

            document = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(document["schema"], "mvp.calibration.v1")


if __name__ == "__main__":
    unittest.main()
