#!/usr/bin/env python3
"""
Barrido de umbrales del reconciliador sobre el conjunto sintético etiquetado.

Selecciona `MIN_LINK_SCORE` y `AMBIGUITY_MARGIN` usando **solo** la partición
de calibración, elige `REVIEW_THRESHOLD` según la carga de revisión y reporta
las métricas finales sobre la partición de evaluación, que nunca participa de
la selección.

El corpus es sintético: la medición demuestra la metodología de calibración,
no el desempeño del pipeline en una organización real.

Uso (desde `mvp/`):
    uv run python calibrate.py
    uv run python calibrate.py --min-link-scores 0.45,0.55 --margins 0.05,0.10
"""

import argparse
import contextlib
import io
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src import config
import evaluate
import run_discovery

SCHEMA = "mvp.calibration.v1"
DEFAULT_DATASET = "datasets/sintetico"
DEFAULT_JSON = "output/calibration_report.json"

DEFAULT_MIN_LINK_SCORES = (0.30, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70)
DEFAULT_AMBIGUITY_MARGINS = (0.01, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20)
DEFAULT_REVIEW_THRESHOLDS = (0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95)

CALIBRATION_SPLIT = "calibration"
EVALUATION_SPLIT = "evaluation"


# ---------------------------------------------------------------------------
# Utilidades de datos y rejilla
# ---------------------------------------------------------------------------

def _resolve_path(value: str) -> Path:
    """Resuelve rutas relativas contra el directorio `mvp/`."""
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def _dataset_label(dataset_dir: Path) -> str:
    """Ruta del conjunto relativa a `mvp/`, estable entre ejecuciones."""
    resolved = Path(dataset_dir).resolve()
    try:
        return resolved.relative_to(BASE_DIR).as_posix()
    except ValueError:
        return Path(os.path.relpath(resolved, BASE_DIR)).as_posix()


def _validate_dataset(dataset_dir: Path) -> None:
    """Verifica que el conjunto tenga las rutas mínimas que consume el pipeline."""
    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"No se encontró el conjunto de datos: {dataset_dir}")
    missing = [
        name for name in (evaluate.REPOS_DIR, evaluate.CONTRACTS_DIR, evaluate.CATALOG_FILE)
        if not (dataset_dir / name).exists()
    ]
    if missing:
        raise FileNotFoundError(
            f"El conjunto {dataset_dir} no contiene: {', '.join(missing)}"
        )


def _normalize_grid(values: Sequence[float], name: str) -> List[float]:
    """Ordena, deduplica y valida una rejilla de umbrales en el rango [0, 1]."""
    normalized: List[float] = []
    for value in values:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError(f"La rejilla {name} contiene un valor no finito: {value}")
        if not 0.0 <= number <= 1.0:
            raise ValueError(f"La rejilla {name} debe estar entre 0 y 1: {number}")
        if number not in normalized:
            normalized.append(number)
    if not normalized:
        raise ValueError(f"La rejilla {name} no puede estar vacía")
    return sorted(normalized)


def filter_items(items: Sequence[Dict[str, Any]], split: str) -> List[Dict[str, Any]]:
    """
    Filtra las etiquetas de una partición.

    Es el único punto donde se separan calibración y evaluación: la selección
    de parámetros recibe exclusivamente las filas de calibración.
    """
    if split == "all":
        return list(items)
    return [item for item in items if item.get("split") == split]


# ---------------------------------------------------------------------------
# Selección de `MIN_LINK_SCORE` y `AMBIGUITY_MARGIN`
# ---------------------------------------------------------------------------

def select_params(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Selecciona los parámetros de vínculo desde filas de **calibración**.

    Regla, en orden:
    1. maximizar la exactitud micro;
    2. desempatar por F1 macro;
    3. desempatar por menor número de conflictos predichos;
    4. dentro del plateau resultante, elegir la mediana por orden
       `(min_link_score, ambiguity_margin)`, no un borde.

    Con un plateau de tamaño par se toma la mediana inferior
    (`(n - 1) // 2`), una convención determinista. Las filas deben provenir
    únicamente de la partición de calibración; la evaluación no se consulta.
    """
    if not rows:
        raise ValueError("No hay filas de calibración para seleccionar parámetros")

    best_accuracy = max(row["accuracy"] for row in rows)
    plateau = [row for row in rows if row["accuracy"] == best_accuracy]

    best_macro_f1 = max(row["macro_f1"] for row in plateau)
    plateau = [row for row in plateau if row["macro_f1"] == best_macro_f1]

    fewest_conflicts = min(row["conflicts"] for row in plateau)
    plateau = [row for row in plateau if row["conflicts"] == fewest_conflicts]

    ordered = sorted(
        plateau,
        key=lambda row: (row["min_link_score"], row["ambiguity_margin"]),
    )
    chosen = ordered[(len(ordered) - 1) // 2]

    rationale = (
        f"Plateau de {len(ordered)} combinación(es) con exactitud máxima "
        f"{best_accuracy:.4f}, F1 macro {best_macro_f1:.4f} y {fewest_conflicts} "
        f"conflicto(s); se elige la mediana por orden (MIN_LINK_SCORE, "
        f"AMBIGUITY_MARGIN) para no favorecer un borde."
    )

    return {
        "min_link_score": chosen["min_link_score"],
        "ambiguity_margin": chosen["ambiguity_margin"],
        "accuracy": chosen["accuracy"],
        "macro_f1": chosen["macro_f1"],
        "conflicts": chosen["conflicts"],
        "plateau_size": len(ordered),
        "rationale": rationale,
    }


# ---------------------------------------------------------------------------
# Selección de `REVIEW_THRESHOLD`
# ---------------------------------------------------------------------------

@contextlib.contextmanager
def _isolated_pipeline_output():
    """
    Redirige las escrituras internas del pipeline a un directorio temporal.

    `run_discovery.run_pipeline` escribe `output/fact_sheets_draft.json` como
    efecto secundario. Este script solo debe dejar el reporte de calibración,
    así que durante el barrido se apunta su `BASE_DIR` a un directorio temporal.
    """
    original = run_discovery.BASE_DIR
    with tempfile.TemporaryDirectory(prefix="apm-calibrate-") as tmp:
        run_discovery.BASE_DIR = Path(tmp)
        try:
            yield
        finally:
            run_discovery.BASE_DIR = original


def _field(obj: Any, name: str, default: Any = None) -> Any:
    """Lee un atributo de un objeto o una clave de un diccionario."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _evidence_ids(fact_sheet: Any) -> List[str]:
    """Identificadores de evidencia vinculados a una hipótesis, sin duplicados."""
    repos = _field(fact_sheet, "linked_repos", []) or []
    contracts = _field(fact_sheet, "linked_contracts", []) or []
    return sorted({str(value) for value in list(repos) + list(contracts)})


def hypothesis_is_wrong(
    fact_sheet: Any,
    labels_by_id: Dict[str, Dict[str, Any]],
    predictions: evaluate.PredictionMap,
) -> bool:
    """
    Determina si una hipótesis auto-publicada es incorrecta.

    Una hipótesis es incorrecta si:
    - alguna de sus evidencias etiquetadas tiene un resultado predicho distinto
      del esperado (error de clasificación), o
    - es espuria: no vincula ninguna evidencia etiquetada, o su `catalog_id` no
      aparece entre los `expected_app_ids` de las evidencias que vincula.

    La comparación es solo de resultado (`linked`, `multi_app`, `orphan`,
    `conflict`); las diferencias de app_ids se reportan aparte con los criterios
    exacto y superconjunto. La función es determinista.
    """
    labeled = [
        labels_by_id[evidence_id]
        for evidence_id in _evidence_ids(fact_sheet)
        if evidence_id in labels_by_id
    ]
    if not labeled:
        return True

    supported_ids = set()
    for item in labeled:
        predicted = predictions.get(item["evidence_id"]) or {}
        if predicted.get("outcome", evaluate.MISSING) != item["expected_outcome"]:
            return True
        supported_ids.update(item.get("expected_app_ids", []) or [])

    catalog_id = _field(fact_sheet, "catalog_id")
    return not catalog_id or catalog_id not in supported_ids


def select_review_threshold(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Elige `REVIEW_THRESHOLD` a partir de la tabla de carga de revisión.

    Regla: el menor umbral con tasa de error cero en lo auto-publicado **y** al
    menos una hipótesis auto-publicada. Un umbral que no publica nada tiene
    tasa indefinida, no cero, y no cuenta como acierto. Si ningún umbral logra
    cero errores, se minimiza el número de errores y se desempata por la menor
    carga de revisión (umbral más alto).
    """
    if not rows:
        raise ValueError("No hay filas de umbral de revisión para seleccionar")

    zero_error = [
        row for row in rows if row["wrong"] == 0 and row.get("auto_published", 0) > 0
    ]
    if zero_error:
        chosen = min(zero_error, key=lambda row: (row["threshold"], row["review_load"]))
        rationale = (
            "Menor umbral con tasa de error 0 entre las hipótesis auto-publicadas; "
            "por encima solo se endurece la carga de revisión sin ganar precisión."
        )
    else:
        candidates = [row for row in rows if row.get("auto_published", 0) > 0] or list(rows)
        chosen = min(
            candidates,
            key=lambda row: (row["wrong"], row["review_load"], row["threshold"]),
        )
        rationale = (
            "Ningún umbral alcanza error 0; se minimiza el número de hipótesis "
            "incorrectas auto-publicadas y se desempata por la menor carga de revisión."
        )

    selection = dict(chosen)
    selection["zero_error"] = bool(zero_error)
    selection["rationale"] = rationale
    return selection


# ---------------------------------------------------------------------------
# Criterios de app_ids
# ---------------------------------------------------------------------------

def app_id_criteria(
    items: Sequence[Dict[str, Any]],
    predictions: evaluate.PredictionMap,
) -> Dict[str, Any]:
    """
    Cuenta la exactitud de app_ids con dos criterios.

    Se evalúan las evidencias cuyo resultado esperado es `linked` o `multi_app`
    y cuyo resultado predicho coincide (igual que `evaluate.compute_metrics`).
    - `exact`: el conjunto esperado es igual al predicho.
    - `superset`: el conjunto esperado está contenido en el predicho.

    `differences` lista los casos que pasan `superset` pero fallan `exact`, es
    decir, los que agregan aplicaciones de más.
    """
    evaluated = 0
    exact_correct = 0
    superset_correct = 0
    differences: List[Dict[str, Any]] = []

    for item in sorted(items, key=lambda value: value["evidence_id"]):
        if item.get("expected_outcome") not in evaluate.APP_ID_OUTCOMES:
            continue
        predicted = predictions.get(item["evidence_id"]) or {}
        if predicted.get("outcome") != item["expected_outcome"]:
            continue

        evaluated += 1
        expected = set(item.get("expected_app_ids", []) or [])
        predicted_ids = set(predicted.get("app_ids", []) or [])
        exact_ok = expected == predicted_ids
        superset_ok = expected <= predicted_ids
        if exact_ok:
            exact_correct += 1
        if superset_ok:
            superset_correct += 1
        if superset_ok and not exact_ok:
            differences.append({
                "evidence_id": item["evidence_id"],
                "expected_app_ids": sorted(expected),
                "predicted_app_ids": sorted(predicted_ids),
                "extra_app_ids": sorted(predicted_ids - expected),
            })

    def _accuracy(correct: int) -> Optional[float]:
        return round(correct / evaluated, 4) if evaluated else None

    return {
        "exact": {
            "evaluated": evaluated,
            "correct": exact_correct,
            "accuracy": _accuracy(exact_correct),
        },
        "superset": {
            "evaluated": evaluated,
            "correct": superset_correct,
            "accuracy": _accuracy(superset_correct),
        },
        "differences": differences,
    }


# ---------------------------------------------------------------------------
# Corrida del pipeline
# ---------------------------------------------------------------------------

def _run_once(
    dataset_dir: Path,
    min_link_score: float,
    ambiguity_margin: float,
    review_threshold: float,
    verbose: bool = False,
) -> Tuple[Dict[str, Any], evaluate.PredictionMap]:
    """Ejecuta el pipeline una vez y devuelve la corrida cruda y las predicciones."""
    kwargs = dict(
        repos_dir=dataset_dir / evaluate.REPOS_DIR,
        contracts_dir=dataset_dir / evaluate.CONTRACTS_DIR,
        catalog_path=dataset_dir / evaluate.CATALOG_FILE,
        review_threshold=review_threshold,
        ambiguity_margin=ambiguity_margin,
        min_link_score=min_link_score,
    )
    if verbose:
        with _isolated_pipeline_output():
            run = run_discovery.run_pipeline(**kwargs)
    else:
        with _isolated_pipeline_output(), contextlib.redirect_stdout(io.StringIO()):
            run = run_discovery.run_pipeline(**kwargs)
    predictions, _ = evaluate.predictions_from_run(run)
    return run, predictions


def _sweep_row(
    min_link_score: float,
    ambiguity_margin: float,
    metrics_result: Dict[str, Any],
    conflicts: int,
    items: Sequence[Dict[str, Any]],
    predictions: evaluate.PredictionMap,
) -> Dict[str, Any]:
    """Construye una fila de barrido con métricas y criterios de app_ids."""
    metrics = metrics_result["metrics"]
    return {
        "min_link_score": min_link_score,
        "ambiguity_margin": ambiguity_margin,
        "accuracy": metrics["micro"]["accuracy"],
        "macro_f1": metrics["macro"]["f1"],
        "macro_precision": metrics["macro"]["precision"],
        "macro_recall": metrics["macro"]["recall"],
        "conflicts": conflicts,
        "per_class": metrics["per_class"],
        "confusion_matrix": metrics_result["confusion_matrix"],
        "app_id": app_id_criteria(items, predictions),
    }


def _summary(metrics_result: Dict[str, Any], conflicts: int) -> Dict[str, Any]:
    """Resumen compacto de una partición para comparaciones."""
    metrics = metrics_result["metrics"]
    return {
        "n": metrics_result["n"],
        "accuracy": metrics["micro"]["accuracy"],
        "macro_f1": metrics["macro"]["f1"],
        "conflicts": conflicts,
    }


# ---------------------------------------------------------------------------
# Construcción del reporte
# ---------------------------------------------------------------------------

def build_report(
    dataset_dir: Union[str, Path],
    min_link_scores: Optional[Sequence[float]] = None,
    ambiguity_margins: Optional[Sequence[float]] = None,
    review_thresholds: Optional[Sequence[float]] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Corre el barrido y construye el reporte determinista de calibración.

    La selección de `MIN_LINK_SCORE` y `AMBIGUITY_MARGIN` usa solo la partición
    de calibración. La partición de evaluación se mide para ambos combos y para
    la configuración actual, pero nunca participa de la selección.
    """
    dataset_path = Path(dataset_dir)
    _validate_dataset(dataset_path)
    labels_document = evaluate.load_labels(dataset_path)
    items = labels_document["items"]

    calibration_items = filter_items(items, CALIBRATION_SPLIT)
    evaluation_items = filter_items(items, EVALUATION_SPLIT)
    if not calibration_items:
        raise ValueError("La partición 'calibration' del conjunto está vacía")
    if not evaluation_items:
        raise ValueError("La partición 'evaluation' del conjunto está vacía")

    link_scores = _normalize_grid(
        DEFAULT_MIN_LINK_SCORES if min_link_scores is None else min_link_scores,
        "MIN_LINK_SCORE",
    )
    margins = _normalize_grid(
        DEFAULT_AMBIGUITY_MARGINS if ambiguity_margins is None else ambiguity_margins,
        "AMBIGUITY_MARGIN",
    )
    thresholds = _normalize_grid(
        DEFAULT_REVIEW_THRESHOLDS if review_thresholds is None else review_thresholds,
        "REVIEW_THRESHOLD",
    )

    calibration_rows: List[Dict[str, Any]] = []
    evaluation_rows: List[Dict[str, Any]] = []
    runs: Dict[Tuple[float, float], Tuple[Dict[str, Any], evaluate.PredictionMap]] = {}

    for min_link_score in link_scores:
        for ambiguity_margin in margins:
            run, predictions = _run_once(
                dataset_path,
                min_link_score,
                ambiguity_margin,
                config.REVIEW_THRESHOLD,
                verbose,
            )
            runs[(min_link_score, ambiguity_margin)] = (run, predictions)
            conflicts = len(run.get("conflicts", []) or [])
            calibration_rows.append(_sweep_row(
                min_link_score,
                ambiguity_margin,
                evaluate.compute_metrics(calibration_items, predictions),
                conflicts,
                calibration_items,
                predictions,
            ))
            evaluation_rows.append(_sweep_row(
                min_link_score,
                ambiguity_margin,
                evaluate.compute_metrics(evaluation_items, predictions),
                conflicts,
                evaluation_items,
                predictions,
            ))

    selection = select_params(calibration_rows)
    selected_key = (selection["min_link_score"], selection["ambiguity_margin"])
    selected_run, selected_predictions = runs[selected_key]

    labels_by_id = {item["evidence_id"]: item for item in calibration_items}
    fact_sheets = selected_run.get("fact_sheets", []) or []
    review_rows: List[Dict[str, Any]] = []
    for threshold in thresholds:
        auto_published = [
            fact_sheet
            for fact_sheet in fact_sheets
            if float(_field(fact_sheet, "confidence_score", 0.0) or 0.0) >= threshold
        ]
        wrong = [
            fact_sheet
            for fact_sheet in auto_published
            if hypothesis_is_wrong(fact_sheet, labels_by_id, selected_predictions)
        ]
        review_rows.append({
            "threshold": threshold,
            "auto_published": len(auto_published),
            "wrong": len(wrong),
            "error_rate": (
                round(len(wrong) / len(auto_published), 4) if auto_published else None
            ),
            "review_load": len(fact_sheets) - len(auto_published),
        })

    review_selection = select_review_threshold(review_rows)

    with _isolated_pipeline_output():
        selected_evaluation = evaluate.evaluate_dataset(
            dataset_path,
            split=EVALUATION_SPLIT,
            min_link_score=selection["min_link_score"],
            ambiguity_margin=selection["ambiguity_margin"],
            review_threshold=review_selection["threshold"],
            verbose=verbose,
        )
        current_evaluation = evaluate.evaluate_dataset(
            dataset_path,
            split=EVALUATION_SPLIT,
            min_link_score=config.MIN_LINK_SCORE,
            ambiguity_margin=config.AMBIGUITY_MARGIN,
            review_threshold=config.REVIEW_THRESHOLD,
            verbose=verbose,
        )

    current_run, current_predictions = _run_once(
        dataset_path,
        config.MIN_LINK_SCORE,
        config.AMBIGUITY_MARGIN,
        config.REVIEW_THRESHOLD,
        verbose,
    )
    current_calibration = evaluate.compute_metrics(calibration_items, current_predictions)
    selected_calibration = evaluate.compute_metrics(calibration_items, selected_predictions)

    return {
        "schema": SCHEMA,
        "dataset": _dataset_label(dataset_path),
        "current_params": {
            "min_link_score": config.MIN_LINK_SCORE,
            "ambiguity_margin": config.AMBIGUITY_MARGIN,
            "review_threshold": config.REVIEW_THRESHOLD,
        },
        "grid": {
            "min_link_scores": link_scores,
            "ambiguity_margins": margins,
            "review_thresholds": thresholds,
        },
        "calibration_rows": calibration_rows,
        "evaluation_rows": evaluation_rows,
        "selection": selection,
        "comparison": {
            "calibration": {
                "selected": _summary(
                    selected_calibration, len(selected_run.get("conflicts", []) or [])
                ),
                "current": _summary(
                    current_calibration, len(current_run.get("conflicts", []) or [])
                ),
            },
        },
        "review_threshold": {
            "rows": review_rows,
            "selection": review_selection,
        },
        "evaluation": {
            "selected": selected_evaluation,
            "current": current_evaluation,
            "app_id_criteria": {
                "selected": app_id_criteria(evaluation_items, selected_predictions),
                "current": app_id_criteria(evaluation_items, current_predictions),
            },
        },
    }


# ---------------------------------------------------------------------------
# Reporte de texto
# ---------------------------------------------------------------------------

def _format_app_accuracy(criteria: Dict[str, Any]) -> str:
    """Formatea una exactitud de app_ids con su conteo."""
    accuracy = criteria["accuracy"]
    if accuracy is None:
        return "sin casos"
    return f"{accuracy:.4f} ({criteria['correct']}/{criteria['evaluated']})"


def _is_selected(row: Dict[str, Any], selection: Dict[str, Any]) -> bool:
    """Indica si una fila corresponde a los parámetros seleccionados."""
    return (
        row["min_link_score"] == selection["min_link_score"]
        and row["ambiguity_margin"] == selection["ambiguity_margin"]
    )


def format_text_report(report: Dict[str, Any]) -> str:
    """Construye el reporte legible del barrido de calibración."""
    selection = report["selection"]
    review = report["review_threshold"]
    review_selection = review["selection"]
    width = 104

    lines = [
        "=" * width,
        "CALIBRACIÓN DEL RECONCILIADOR SOBRE UN CONJUNTO SINTÉTICO ETIQUETADO".center(width),
        "=" * width,
        f"Conjunto: {report['dataset']}",
        (
            "Rejilla: "
            f"{len(report['grid']['min_link_scores'])} x "
            f"{len(report['grid']['ambiguity_margins'])} combinaciones de "
            "MIN_LINK_SCORE x AMBIGUITY_MARGIN; "
            f"{len(report['grid']['review_thresholds'])} umbrales de revisión."
        ),
        "",
        "--- Barrido de calibración (mejores combinaciones por exactitud) ---",
    ]

    ordered_rows = sorted(
        report["calibration_rows"],
        key=lambda row: (
            -row["accuracy"],
            -row["macro_f1"],
            row["conflicts"],
            row["min_link_score"],
            row["ambiguity_margin"],
        ),
    )
    header = (
        f"{'MIN_LINK':>9}{'MARGEN':>9}{'Exactitud':>11}{'F1 macro':>11}"
        f"{'Conflictos':>12}{'AppIDs exacta':>15}{'AppIDs super.':>15}  Marca"
    )
    lines.extend([header, "-" * width])
    for row in ordered_rows[:15]:
        marker = "  <- seleccionado" if _is_selected(row, selection) else ""
        exact = row["app_id"]["exact"]["accuracy"]
        superset = row["app_id"]["superset"]["accuracy"]
        lines.append(
            f"{row['min_link_score']:>9.2f}{row['ambiguity_margin']:>9.2f}"
            f"{row['accuracy']:>11.4f}{row['macro_f1']:>11.4f}{row['conflicts']:>12d}"
            f"{(f'{exact:.4f}' if exact is not None else '-'):>15}"
            f"{(f'{superset:.4f}' if superset is not None else '-'):>15}{marker}"
        )
    if len(ordered_rows) > 15:
        lines.append(f"... {len(ordered_rows) - 15} combinaciones adicionales en el JSON.")
    lines.append("")
    lines.append(
        f"Plateau seleccionado: {selection['plateau_size']} combinación(es). "
        f"Parámetros: MIN_LINK_SCORE={selection['min_link_score']:.2f}, "
        f"AMBIGUITY_MARGIN={selection['ambiguity_margin']:.2f}."
    )
    lines.append(f"Justificación: {selection['rationale']}")

    comparison = report["comparison"]["calibration"]
    lines.extend([
        "",
        "--- Configuración actual frente a la seleccionada (calibración) ---",
        (
            f"{'Configuración':<18}{'MIN_LINK':>9}{'MARGEN':>9}{'Exactitud':>11}"
            f"{'F1 macro':>11}{'Conflictos':>12}{'n':>6}"
        ),
        "-" * width,
        (
            f"{'actual':<18}{report['current_params']['min_link_score']:>9.2f}"
            f"{report['current_params']['ambiguity_margin']:>9.2f}"
            f"{comparison['current']['accuracy']:>11.4f}"
            f"{comparison['current']['macro_f1']:>11.4f}"
            f"{comparison['current']['conflicts']:>12d}{comparison['current']['n']:>6d}"
        ),
        (
            f"{'seleccionada':<18}{selection['min_link_score']:>9.2f}"
            f"{selection['ambiguity_margin']:>9.2f}"
            f"{comparison['selected']['accuracy']:>11.4f}"
            f"{comparison['selected']['macro_f1']:>11.4f}"
            f"{comparison['selected']['conflicts']:>12d}{comparison['selected']['n']:>6d}"
        ),
        "",
        "--- REVIEW_THRESHOLD: auto-publicado frente a carga de revisión ---",
        (
            f"{'Umbral':>8}{'Auto-publicadas':>17}{'Incorrectas':>14}"
            f"{'Tasa error':>13}{'Carga revisión':>16}  Marca"
        ),
        "-" * width,
    ])
    for row in review["rows"]:
        marker = "  <- seleccionado" if row["threshold"] == review_selection["threshold"] else ""
        error_rate = (
            f"{row['error_rate']:.4f}" if row["error_rate"] is not None else "n/d"
        )
        lines.append(
            f"{row['threshold']:>8.2f}{row['auto_published']:>17d}{row['wrong']:>14d}"
            f"{error_rate:>13}{row['review_load']:>16d}{marker}"
        )
    lines.append("")
    lines.append(
        f"Decisión: REVIEW_THRESHOLD={review_selection['threshold']:.2f} "
        f"(auto-publicadas={review_selection['auto_published']}, "
        f"incorrectas={review_selection['wrong']}, "
        f"carga de revisión={review_selection['review_load']})."
    )
    lines.append(f"Justificación: {review_selection['rationale']}")
    lines.append(
        "Criterio de 'incorrecta': hipótesis con alguna evidencia etiquetada cuyo "
        "resultado predicho difiere del esperado, o hipótesis espuria sin anclaje "
        "verificable; no cuenta diferencias de app_ids (se reportan aparte)."
    )

    lines.extend([
        "",
        "--- Evaluación sobre la partición reservada (no usada para seleccionar) ---",
    ])
    app_criteria = report["evaluation"]["app_id_criteria"]
    for name, key, params in (
        ("seleccionada", "selected", {
            "min_link_score": selection["min_link_score"],
            "ambiguity_margin": selection["ambiguity_margin"],
            "review_threshold": review_selection["threshold"],
        }),
        ("actual", "current", report["current_params"]),
    ):
        evaluation = report["evaluation"][key]
        result = evaluation["splits"][EVALUATION_SPLIT]
        metrics = result["metrics"]
        criteria = app_criteria[key]
        lines.append(
            f"Configuración {name}: MIN_LINK_SCORE={params['min_link_score']:.2f} | "
            f"AMBIGUITY_MARGIN={params['ambiguity_margin']:.2f} | "
            f"REVIEW_THRESHOLD={params['review_threshold']:.2f}"
        )
        lines.append(
            f"  n={result['n']} | exactitud micro={metrics['micro']['accuracy']:.4f} | "
            f"F1 macro={metrics['macro']['f1']:.4f} | "
            f"app_ids exacta={_format_app_accuracy(criteria['exact'])} | "
            f"app_ids superconjunto={_format_app_accuracy(criteria['superset'])}"
        )
        differences = criteria["differences"]
        if differences:
            detail = "; ".join(
                f"{difference['evidence_id']} (esperado={difference['expected_app_ids']}, "
                f"predicho={difference['predicted_app_ids']})"
                for difference in differences
            )
            lines.append(f"  Diferencias exacto/superconjunto: {detail}")
        else:
            lines.append("  Diferencias exacto/superconjunto: ninguna")
        lines.append("")

    lines.extend([
        "--- Propuesta para mvp/src/config.py (NO aplicada por este script) ---",
        f"REVIEW_THRESHOLD: float = {review_selection['threshold']:.2f}",
        f"MIN_LINK_SCORE: float = {selection['min_link_score']:.2f}",
        f"AMBIGUITY_MARGIN: float = {selection['ambiguity_margin']:.2f}",
        "",
    ])
    if selection["min_link_score"] >= review_selection["threshold"]:
        lines.append(
            "ADVERTENCIA: MIN_LINK_SCORE no es menor que REVIEW_THRESHOLD; "
            "revisar la relación entre ambos umbrales antes de aplicar el cambio."
        )
        lines.append("")
    lines.append(
        "Nota: el corpus es sintético y la partición de calibración es pequeña; "
        "las diferencias de una sola evidencia son ruido de medición."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_float_list(raw: str, label: str) -> List[float]:
    """Parsea una lista separada por comas y valida cada valor."""
    values: List[float] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            raise ValueError(f"La lista {label} contiene un valor vacío")
        try:
            values.append(float(token))
        except ValueError as exc:
            raise ValueError(f"Valor no numérico en {label}: '{token}'") from exc
    return _normalize_grid(values, label)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada CLI. Devuelve 0 salvo errores de datos, rejilla o E/S."""
    parser = argparse.ArgumentParser(
        description="Calibra los umbrales del reconciliador sobre un conjunto etiquetado."
    )
    parser.add_argument(
        "--dataset", default=DEFAULT_DATASET,
        help=f"Ruta del conjunto (por defecto: {DEFAULT_DATASET})",
    )
    parser.add_argument(
        "--json", dest="json_path", default=DEFAULT_JSON,
        help=f"Ruta del reporte JSON (por defecto: {DEFAULT_JSON})",
    )
    parser.add_argument(
        "--min-link-scores", default=None,
        help="Lista de MIN_LINK_SCORE separada por comas (por defecto: rejilla estándar)",
    )
    parser.add_argument(
        "--margins", default=None,
        help="Lista de AMBIGUITY_MARGIN separada por comas (por defecto: rejilla estándar)",
    )
    parser.add_argument(
        "--review-thresholds", default=None,
        help="Lista de REVIEW_THRESHOLD separada por comas (por defecto: rejilla estándar)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Muestra la salida completa del pipeline",
    )
    args = parser.parse_args(argv)

    dataset_path = _resolve_path(args.dataset)
    json_path = _resolve_path(args.json_path)

    try:
        min_link_scores = (
            _parse_float_list(args.min_link_scores, "MIN_LINK_SCORE")
            if args.min_link_scores is not None else None
        )
        ambiguity_margins = (
            _parse_float_list(args.margins, "AMBIGUITY_MARGIN")
            if args.margins is not None else None
        )
        review_thresholds = (
            _parse_float_list(args.review_thresholds, "REVIEW_THRESHOLD")
            if args.review_thresholds is not None else None
        )
        report = build_report(
            dataset_path,
            min_link_scores=min_link_scores,
            ambiguity_margins=ambiguity_margins,
            review_thresholds=review_thresholds,
            verbose=args.verbose,
        )
        destination = evaluate.write_report(report, json_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(format_text_report(report))
    print(f"\nReporte JSON escrito en: {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
