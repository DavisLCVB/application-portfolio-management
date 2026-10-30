#!/usr/bin/env python3
"""
Evaluador del pipeline de descubrimiento sobre el conjunto sintético etiquetado.

Corre el pipeline una sola vez sobre un conjunto con verdad conocida
(`labels.json`), mapea cada evidencia a un resultado (vinculada, multi-aplicación,
huérfana o conflicto) y reporta precisión, recall, F1, matriz de confusión y
exactitud del conjunto de app_ids.

El corpus es sintético: la medición evalúa la metodología de calibración, no el
desempeño del pipeline en una organización real.

Uso (desde `mvp/`):
    uv run python evaluate.py
    uv run python evaluate.py --split evaluation --json /tmp/reporte.json
"""

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src import config
import run_discovery

SCHEMA = "mvp.evaluation.v1"
OUTCOMES = ("linked", "multi_app", "orphan", "conflict")
MISSING = "missing"
COLUMNS = OUTCOMES + (MISSING,)
SPLIT_CHOICES = ("both", "evaluation", "calibration", "all")
APP_ID_OUTCOMES = ("linked", "multi_app")

DEFAULT_DATASET = "datasets/sintetico"
DEFAULT_JSON = "output/evaluation_report.json"
LABELS_FILE = "labels.json"
REPOS_DIR = "repos"
CONTRACTS_DIR = "contratos"
CATALOG_FILE = "catalogo_aplicaciones.csv"

Prediction = Dict[str, Any]
PredictionMap = Dict[str, Prediction]


# ---------------------------------------------------------------------------
# Carga y corrida del pipeline
# ---------------------------------------------------------------------------

def load_labels(dataset_dir: Path) -> Dict[str, Any]:
    """Carga `labels.json` del conjunto. Lanza un error legible si no es válido."""
    labels_path = Path(dataset_dir) / LABELS_FILE
    if not labels_path.is_file():
        raise FileNotFoundError(f"No se encontró el archivo de etiquetas: {labels_path}")
    try:
        with open(labels_path, "r", encoding="utf-8") as handle:
            labels = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ValueError(f"El archivo de etiquetas no es JSON válido: {labels_path} ({exc})") from exc
    if not isinstance(labels, dict) or not isinstance(labels.get("items"), list):
        raise ValueError(f"El archivo de etiquetas no tiene la estructura esperada: {labels_path}")
    return labels


def _validate_dataset(dataset_dir: Path) -> None:
    """Verifica que el conjunto tenga las rutas mínimas que consume el pipeline."""
    if not dataset_dir.is_dir():
        raise FileNotFoundError(f"No se encontró el conjunto de datos: {dataset_dir}")
    missing = [
        name for name in (REPOS_DIR, CONTRACTS_DIR, CATALOG_FILE)
        if not (dataset_dir / name).exists()
    ]
    if missing:
        raise FileNotFoundError(
            f"El conjunto {dataset_dir} no contiene: {', '.join(missing)}"
        )


def _read(obj: Any, name: str, default: Any = None) -> Any:
    """Lee un atributo de un objeto o una clave de un diccionario."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _candidate_code(candidate: Any) -> Optional[str]:
    """Obtiene el código de catálogo de un candidato de conflicto."""
    code = _read(candidate, "catalog_id") or _read(candidate, "code")
    return str(code) if code else None


def _dedupe(values: Iterable[str]) -> List[str]:
    """Elimina duplicados preservando el orden de aparición."""
    seen: Set[str] = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def predictions_from_run(
    run: Dict[str, Any],
) -> Tuple[PredictionMap, List[Dict[str, Any]]]:
    """
    Convierte la salida de `run_pipeline` en predicciones por evidencia.

    Precedencia: conflicto > contrato multi-aplicación > huérfano > vínculo.
    Un identificador reclamado por varias hipótesis conserva la de mayor
    confianza y se reporta como anomalía en `multi_claim`.
    """
    conflict_predictions: Dict[str, List[str]] = {}
    for conflict in run.get("conflicts", []) or []:
        evidence_id = _read(conflict, "name")
        if not evidence_id:
            continue
        codes = [_candidate_code(c) for c in (_read(conflict, "candidates", []) or [])]
        conflict_predictions.setdefault(
            str(evidence_id),
            _dedupe(code for code in codes if code),
        )

    multi_codes: Dict[str, Set[str]] = {}
    linked_claims: Dict[str, List[Tuple[str, float]]] = {}

    for fact_sheet in run.get("fact_sheets", []) or []:
        catalog_id = _read(fact_sheet, "catalog_id")
        confidence = float(_read(fact_sheet, "confidence_score", 0.0) or 0.0)

        mapping = _read(fact_sheet, "multi_application_contracts", {}) or {}
        if isinstance(mapping, dict):
            for doc_id, codes in mapping.items():
                multi_codes.setdefault(str(doc_id), set()).update(
                    str(code) for code in (codes or [])
                )

        if not catalog_id:
            continue
        for repo_name in _read(fact_sheet, "linked_repos", []) or []:
            linked_claims.setdefault(str(repo_name), []).append((str(catalog_id), confidence))
        for doc_id in _read(fact_sheet, "linked_contracts", []) or []:
            linked_claims.setdefault(str(doc_id), []).append((str(catalog_id), confidence))

    orphan_names = {
        str(_read(orphan, "name"))
        for orphan in (run.get("orphans", []) or [])
        if _read(orphan, "name")
    }

    predictions: PredictionMap = {}
    for evidence_id in sorted(conflict_predictions):
        predictions[evidence_id] = {
            "outcome": "conflict",
            "app_ids": conflict_predictions[evidence_id],
        }
    for evidence_id in sorted(multi_codes):
        if evidence_id not in predictions:
            predictions[evidence_id] = {
                "outcome": "multi_app",
                "app_ids": sorted(multi_codes[evidence_id]),
            }
    for evidence_id in sorted(orphan_names):
        if evidence_id not in predictions:
            predictions[evidence_id] = {"outcome": "orphan", "app_ids": []}

    multi_claim: List[Dict[str, Any]] = []
    for evidence_id in sorted(linked_claims):
        if evidence_id in predictions:
            continue
        claims = linked_claims[evidence_id]
        best_catalog_id, _ = max(claims, key=lambda claim: (claim[1], claim[0]))
        predictions[evidence_id] = {
            "outcome": "linked",
            "app_ids": [best_catalog_id],
        }
        distinct = {catalog_id for catalog_id, _ in claims}
        if len(distinct) > 1:
            multi_claim.append({
                "evidence_id": evidence_id,
                "predicted": best_catalog_id,
                "hypotheses": [
                    {"catalog_id": catalog_id, "confidence_score": confidence}
                    for catalog_id, confidence in sorted(claims, key=lambda c: (-c[1], c[0]))
                ],
            })

    return predictions, multi_claim


def _run_and_predict(
    dataset_dir: Path,
    min_link_score: float,
    ambiguity_margin: float,
    review_threshold: float,
    verbose: bool,
) -> Tuple[PredictionMap, List[Dict[str, Any]]]:
    """Ejecuta el pipeline una vez y devuelve las predicciones por evidencia."""
    if verbose:
        run = run_discovery.run_pipeline(
            repos_dir=dataset_dir / REPOS_DIR,
            contracts_dir=dataset_dir / CONTRACTS_DIR,
            catalog_path=dataset_dir / CATALOG_FILE,
            review_threshold=review_threshold,
            ambiguity_margin=ambiguity_margin,
            min_link_score=min_link_score,
        )
    else:
        with contextlib.redirect_stdout(io.StringIO()):
            run = run_discovery.run_pipeline(
                repos_dir=dataset_dir / REPOS_DIR,
                contracts_dir=dataset_dir / CONTRACTS_DIR,
                catalog_path=dataset_dir / CATALOG_FILE,
                review_threshold=review_threshold,
                ambiguity_margin=ambiguity_margin,
                min_link_score=min_link_score,
            )
    return predictions_from_run(run)


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------

def _ratio(numerator: float, denominator: float) -> float:
    """División segura redondeada a cuatro decimales."""
    return round(numerator / denominator, 4) if denominator else 0.0


def compute_metrics(
    labels: Sequence[Dict[str, Any]],
    predictions: PredictionMap,
) -> Dict[str, Any]:
    """
    Calcula la matriz de confusión y las métricas de una partición.

    Las filas son el resultado esperado y las columnas el predicho, más la
    pseudo-columna `missing` para la evidencia sin predicción. El promedio
    macro recorre las cuatro clases; el micro equivale a la exactitud.
    """
    rows = {expected: {column: 0 for column in COLUMNS} for expected in OUTCOMES}
    true_positive = {outcome: 0 for outcome in OUTCOMES}
    false_positive = {outcome: 0 for outcome in OUTCOMES}
    false_negative = {outcome: 0 for outcome in OUTCOMES}
    support = {outcome: 0 for outcome in OUTCOMES}

    app_evaluated = 0
    app_correct = 0
    app_mismatches: List[Dict[str, Any]] = []

    for item in labels:
        evidence_id = item["evidence_id"]
        expected = item["expected_outcome"]
        predicted = (predictions.get(evidence_id) or {}).get("outcome", MISSING)
        if predicted not in COLUMNS:
            predicted = MISSING

        if expected in rows:
            rows[expected][predicted] += 1

        if expected not in OUTCOMES:
            continue

        support[expected] += 1
        if predicted == expected:
            true_positive[expected] += 1
        else:
            false_negative[expected] += 1
            if predicted in OUTCOMES:
                false_positive[predicted] += 1

        if expected in APP_ID_OUTCOMES and predicted == expected:
            app_evaluated += 1
            expected_ids = set(item.get("expected_app_ids", []) or [])
            predicted_ids = set((predictions.get(evidence_id) or {}).get("app_ids", []) or [])
            if expected_ids == predicted_ids:
                app_correct += 1
            else:
                app_mismatches.append({
                    "evidence_id": evidence_id,
                    "expected_app_ids": sorted(expected_ids),
                    "predicted_app_ids": sorted(predicted_ids),
                })

    per_class: Dict[str, Dict[str, Any]] = {}
    raw_precision: Dict[str, float] = {}
    raw_recall: Dict[str, float] = {}
    raw_f1: Dict[str, float] = {}
    for outcome in OUTCOMES:
        tp = true_positive[outcome]
        fp = false_positive[outcome]
        fn = false_negative[outcome]
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        raw_precision[outcome] = precision
        raw_recall[outcome] = recall
        raw_f1[outcome] = f1
        per_class[outcome] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support[outcome],
        }

    total = len(labels)
    correct = sum(true_positive.values())
    accuracy = correct / total if total else 0.0

    return {
        "n": total,
        "metrics": {
            "per_class": per_class,
            "macro": {
                "precision": round(sum(raw_precision.values()) / len(OUTCOMES), 4),
                "recall": round(sum(raw_recall.values()) / len(OUTCOMES), 4),
                "f1": round(sum(raw_f1.values()) / len(OUTCOMES), 4),
            },
            "micro": {
                "precision": round(accuracy, 4),
                "recall": round(accuracy, 4),
                "f1": round(accuracy, 4),
                "accuracy": round(accuracy, 4),
            },
            "app_id_accuracy": {
                "evaluated": app_evaluated,
                "correct": app_correct,
                "accuracy": round(app_correct / app_evaluated, 4) if app_evaluated else None,
            },
        },
        "confusion_matrix": {
            "classes": list(OUTCOMES),
            "columns": list(COLUMNS),
            "rows": rows,
        },
        "app_id_mismatches": sorted(app_mismatches, key=lambda error: error["evidence_id"]),
    }


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------

def _dataset_label(dataset_dir: Path) -> str:
    """Ruta del conjunto relativa a `mvp/`, estable entre ejecuciones."""
    resolved = dataset_dir.resolve()
    try:
        return resolved.relative_to(BASE_DIR).as_posix()
    except ValueError:
        return Path(os.path.relpath(resolved, BASE_DIR)).as_posix()


def _splits_to_compute(split: str) -> List[str]:
    """Particiones que se calculan y guardan en el reporte JSON."""
    if split == "both":
        return ["evaluation", "calibration", "all"]
    return [split]


def _subset(items: Sequence[Dict[str, Any]], split: str) -> List[Dict[str, Any]]:
    """Filtra las etiquetas de una partición; `all` incluye todas."""
    if split == "all":
        return list(items)
    return [item for item in items if item.get("split") == split]


def evaluate_dataset(
    dataset_dir: Union[str, Path],
    split: str = "both",
    min_link_score: Optional[float] = None,
    ambiguity_margin: Optional[float] = None,
    review_threshold: Optional[float] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Corre el pipeline una vez y construye el reporte de evaluación determinista.

    No imprime la salida del pipeline salvo con `verbose=True`.
    """
    if split not in SPLIT_CHOICES:
        raise ValueError(f"Partición no válida: {split}. Opciones: {', '.join(SPLIT_CHOICES)}")

    dataset_path = Path(dataset_dir)
    _validate_dataset(dataset_path)
    labels_document = load_labels(dataset_path)
    items = labels_document["items"]

    resolved_min_link = config.MIN_LINK_SCORE if min_link_score is None else float(min_link_score)
    resolved_margin = config.AMBIGUITY_MARGIN if ambiguity_margin is None else float(ambiguity_margin)
    resolved_review = config.REVIEW_THRESHOLD if review_threshold is None else float(review_threshold)

    predictions, multi_claim = _run_and_predict(
        dataset_path,
        resolved_min_link,
        resolved_margin,
        resolved_review,
        verbose,
    )

    splits: Dict[str, Any] = {}
    selected_ids: Set[str] = set()
    app_mismatches: List[Dict[str, Any]] = []
    computed = _splits_to_compute(split)

    for name in computed:
        subset = _subset(items, name)
        result = compute_metrics(subset, predictions)
        mismatches = result.pop("app_id_mismatches")
        # En `both`, la partición `all` es la unión de las otras dos: no duplicar errores.
        if not (split == "both" and name == "all"):
            app_mismatches.extend(mismatches)
        selected_ids.update(item["evidence_id"] for item in subset)
        splits[name] = result

    labeled_ids = {item["evidence_id"] for item in items}
    missing_predictions = sorted(selected_ids - set(predictions))
    unlabeled_predictions = sorted(set(predictions) - labeled_ids)
    selected_multi_claim = sorted(
        (error for error in multi_claim if error["evidence_id"] in selected_ids),
        key=lambda error: error["evidence_id"],
    )

    return {
        "schema": SCHEMA,
        "dataset": _dataset_label(dataset_path),
        "params": {
            "min_link_score": resolved_min_link,
            "ambiguity_margin": resolved_margin,
            "review_threshold": resolved_review,
        },
        "splits": splits,
        "errors": {
            "missing_predictions": missing_predictions,
            "unlabeled_predictions": unlabeled_predictions,
            "app_id_mismatches": sorted(app_mismatches, key=lambda error: error["evidence_id"]),
            "multi_claim": selected_multi_claim,
        },
    }


def write_report(report: Dict[str, Any], json_path: Union[str, Path]) -> Path:
    """Escribe el reporte JSON (sin marcas de tiempo) y devuelve la ruta."""
    destination = Path(json_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with open(destination, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return destination


def _format_metrics_table(result: Dict[str, Any]) -> List[str]:
    """Renderiza la tabla de métricas por clase de una partición."""
    lines = [
        f"{'Clase':<12}{'Precisión':>11}{'Recall':>10}{'F1':>10}{'Soporte':>10}",
        "-" * 53,
    ]
    for outcome in OUTCOMES:
        values = result["metrics"]["per_class"][outcome]
        lines.append(
            f"{outcome:<12}{values['precision']:>11.4f}{values['recall']:>10.4f}"
            f"{values['f1']:>10.4f}{values['support']:>10d}"
        )
    macro = result["metrics"]["macro"]
    micro = result["metrics"]["micro"]
    lines.append("-" * 53)
    lines.append(
        f"{'Macro':<12}{macro['precision']:>11.4f}{macro['recall']:>10.4f}{macro['f1']:>10.4f}{'':>10}"
    )
    lines.append(
        f"{'Micro':<12}{micro['precision']:>11.4f}{micro['recall']:>10.4f}{micro['f1']:>10.4f}{'':>10}"
    )
    lines.append(f"Exactitud (micro): {micro['accuracy']:.4f}")
    app_accuracy = result["metrics"]["app_id_accuracy"]
    if app_accuracy["accuracy"] is None:
        lines.append("Exactitud de app_ids: sin casos evaluables")
    else:
        lines.append(
            f"Exactitud de app_ids: {app_accuracy['accuracy']:.4f} "
            f"({app_accuracy['correct']}/{app_accuracy['evaluated']})"
        )
    return lines


def _format_confusion_matrix(result: Dict[str, Any]) -> List[str]:
    """Renderiza la matriz de confusión con la columna `missing`."""
    matrix = result["confusion_matrix"]
    columns = matrix["columns"]
    width = 12
    header = f"{'esperado\\predicho':<{width}}" + "".join(f"{column:>{width}}" for column in columns)
    lines = [header, "-" * len(header)]
    for expected in matrix["classes"]:
        row = matrix["rows"][expected]
        lines.append(
            f"{expected:<{width}}" + "".join(f"{row[column]:>{width}d}" for column in columns)
        )
    return lines


def _format_errors(errors: Dict[str, Any]) -> List[str]:
    """Renderiza el listado de anomalías de la evaluación."""
    lines = ["Errores:"]
    missing = errors.get("missing_predictions", [])
    lines.append(f"  Sin predicción ({len(missing)}): {', '.join(missing) if missing else 'ninguno'}")
    unlabeled = errors.get("unlabeled_predictions", [])
    lines.append(
        f"  Predicciones sin etiqueta ({len(unlabeled)}): "
        f"{', '.join(unlabeled) if unlabeled else 'ninguno'}"
    )
    mismatches = errors.get("app_id_mismatches", [])
    lines.append(f"  app_ids incorrectos ({len(mismatches)}):")
    if not mismatches:
        lines.append("    ninguno")
    for error in mismatches:
        lines.append(
            f"    {error['evidence_id']}: esperado={error['expected_app_ids']} "
            f"predicho={error['predicted_app_ids']}"
        )
    claims = errors.get("multi_claim", [])
    lines.append(f"  Reclamada por varias hipótesis ({len(claims)}):")
    if not claims:
        lines.append("    ninguno")
    for error in claims:
        detail = ", ".join(
            f"{hypothesis['catalog_id']} ({hypothesis['confidence_score']:.3f})"
            for hypothesis in error["hypotheses"]
        )
        lines.append(f"    {error['evidence_id']}: predicho={error['predicted']} | {detail}")
    return lines


def format_text_report(report: Dict[str, Any]) -> str:
    """Construye el reporte legible de la evaluación."""
    lines = [
        "=" * 88,
        "EVALUACIÓN DEL PIPELINE DE DESCUBRIMIENTO SOBRE UN CONJUNTO ETIQUETADO".center(88),
        "=" * 88,
        f"Conjunto: {report['dataset']}",
        (
            f"Parámetros: MIN_LINK_SCORE={report['params']['min_link_score']:.2f} | "
            f"AMBIGUITY_MARGIN={report['params']['ambiguity_margin']:.2f} | "
            f"REVIEW_THRESHOLD={report['params']['review_threshold']:.2f}"
        ),
        "",
    ]

    preferred_order = ["evaluation", "calibration", "all"]
    for name in preferred_order:
        if name not in report["splits"]:
            continue
        result = report["splits"][name]
        lines.append(f"--- Partición: {name} (n={result['n']}) ---")
        lines.extend(_format_metrics_table(result))
        lines.append("")
        lines.append("Matriz de confusión (filas = esperado, columnas = predicho):")
        lines.extend(_format_confusion_matrix(result))
        lines.append("")

    lines.extend(_format_errors(report["errors"]))
    lines.append("")
    lines.append(
        "Nota: el corpus es sintético; esta medición evalúa la metodología de "
        "calibración, no el desempeño en una organización real."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _resolve_path(value: str) -> Path:
    """Resuelve rutas relativas contra el directorio `mvp/`."""
    path = Path(value)
    return path if path.is_absolute() else BASE_DIR / path


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada CLI. Devuelve 0 salvo errores reales de datos o E/S."""
    parser = argparse.ArgumentParser(
        description="Evalúa el pipeline de descubrimiento contra un conjunto etiquetado."
    )
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help=f"Ruta del conjunto (por defecto: {DEFAULT_DATASET})")
    parser.add_argument("--json", dest="json_path", default=DEFAULT_JSON, help=f"Ruta del reporte JSON (por defecto: {DEFAULT_JSON})")
    parser.add_argument("--split", choices=SPLIT_CHOICES, default="both", help="Partición a reportar (por defecto: both)")
    parser.add_argument("--min-link-score", type=float, default=None, help="Score mínimo de vinculación (por defecto: config.MIN_LINK_SCORE)")
    parser.add_argument("--ambiguity-margin", type=float, default=None, help="Margen de conflicto (por defecto: config.AMBIGUITY_MARGIN)")
    parser.add_argument("--review-threshold", type=float, default=None, help="Umbral de revisión (por defecto: config.REVIEW_THRESHOLD)")
    parser.add_argument("--verbose", action="store_true", help="Muestra la salida completa del pipeline")
    args = parser.parse_args(argv)

    dataset_path = _resolve_path(args.dataset)
    json_path = _resolve_path(args.json_path)

    try:
        report = evaluate_dataset(
            dataset_path,
            split=args.split,
            min_link_score=args.min_link_score,
            ambiguity_margin=args.ambiguity_margin,
            review_threshold=args.review_threshold,
            verbose=args.verbose,
        )
        destination = write_report(report, json_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(format_text_report(report))
    print(f"\nReporte JSON escrito en: {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
