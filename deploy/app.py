"""
API mínima (FastAPI) que envuelve el pipeline de descubrimiento del MVP.

Expone:
- GET  /health    → estado del servicio y umbrales vigentes.
- POST /discover  → ejecuta el pipeline (fixtures por defecto o rutas propias)
                    y devuelve Fact Sheets, nudges, huérfanos y conflictos en JSON.
- POST /calibrate → ejecuta el barrido de calibración sobre el conjunto
                    sintético etiquetado y devuelve el reporte.

No modifica la lógica del MVP: solo añade una capa HTTP. La escritura de
artefactos del pipeline se redirige a un directorio temporal porque el
filesystem de Cloud Run es de solo lectura salvo `/tmp`.

Uso local:
    cd deploy
    pip install -r requirements.txt
    uvicorn app:app --reload
"""

import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Hacer importable el paquete del MVP (mvp/ está un nivel por encima de deploy/).
MVP_DIR = Path(__file__).resolve().parent.parent / "mvp"
if str(MVP_DIR) not in sys.path:
    sys.path.insert(0, str(MVP_DIR))

import calibrate  # noqa: E402
import run_discovery  # noqa: E402
from src import config  # noqa: E402

app = FastAPI(title="APM Discovery MVP", version="0.1.0")

# Rejilla pequeña por defecto para /calibrate: mantiene el endpoint responsive
# en serverless. La rejilla completa (7x7) se puede pedir explícitamente.
API_CALIBRATION_GRID = {
    "min_link_scores": [0.45, 0.55],
    "ambiguity_margins": [0.05, 0.15],
    "review_thresholds": [0.70, 0.90],
}


class DiscoverRequest(BaseModel):
    """Parámetros opcionales para /discover; vacío = fixtures canónicos."""

    repos_dir: Optional[str] = None
    contracts_dir: Optional[str] = None
    diagrams_dir: Optional[str] = None
    catalog_path: Optional[str] = None
    review_threshold: Optional[float] = None
    ambiguity_margin: Optional[float] = None
    min_link_score: Optional[float] = None


class CalibrateRequest(BaseModel):
    """Rejilla opcional para /calibrate; listas separadas por comas."""

    min_link_scores: Optional[str] = None
    ambiguity_margins: Optional[str] = None
    review_thresholds: Optional[str] = None


def _parse_csv(raw: Optional[str]) -> Optional[List[float]]:
    """Parsea '0.45,0.55' en [0.45, 0.55]; None o vacío → None."""
    if not raw:
        return None
    values = [float(token.strip()) for token in raw.split(",") if token.strip()]
    return values or None


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "config": {
            "review_threshold": config.REVIEW_THRESHOLD,
            "min_link_score": config.MIN_LINK_SCORE,
            "ambiguity_margin": config.AMBIGUITY_MARGIN,
        },
    }


@app.post("/discover")
def discover(request: Optional[DiscoverRequest] = None) -> Dict[str, Any]:
    req = request or DiscoverRequest()
    with tempfile.TemporaryDirectory(prefix="apm-discover-") as tmp:
        result = run_discovery.run_pipeline(
            repos_dir=req.repos_dir,
            contracts_dir=req.contracts_dir,
            diagrams_dir=req.diagrams_dir,
            catalog_path=req.catalog_path,
            review_threshold=(
                req.review_threshold if req.review_threshold is not None else config.REVIEW_THRESHOLD
            ),
            ambiguity_margin=(
                req.ambiguity_margin if req.ambiguity_margin is not None else config.AMBIGUITY_MARGIN
            ),
            min_link_score=req.min_link_score,
            output_dir=tmp,
        )

    fact_sheets = result.get("fact_sheets", [])
    nudges = result.get("nudges", [])
    orphans = result.get("orphans", [])
    conflicts = result.get("conflicts", [])
    diagrams = result.get("diagrams", [])

    return {
        "fact_sheets": [fs.to_dict() for fs in fact_sheets],
        "micro_nudges": [n.to_dict() for n in nudges],
        "orphan_candidates": [o.to_dict() for o in orphans],
        "conflicts": [c.to_dict() for c in conflicts],
        "diagram_evidences": [d.to_dict() for d in diagrams],
        "counts": {
            "hypotheses": len(fact_sheets),
            "micro_nudges": len(nudges),
            "orphans": len(orphans),
            "conflicts": len(conflicts),
            "diagrams": len(diagrams),
        },
    }


@app.post("/calibrate")
def calibrate_endpoint(request: Optional[CalibrateRequest] = None) -> Dict[str, Any]:
    req = request or CalibrateRequest()
    dataset = MVP_DIR / "datasets" / "sintetico"

    report = calibrate.build_report(
        dataset,
        min_link_scores=_parse_csv(req.min_link_scores) or API_CALIBRATION_GRID["min_link_scores"],
        ambiguity_margins=_parse_csv(req.ambiguity_margins) or API_CALIBRATION_GRID["ambiguity_margins"],
        review_thresholds=_parse_csv(req.review_thresholds) or API_CALIBRATION_GRID["review_thresholds"],
    )

    # El reporte completo es grande (~200 KB); se devuelve un resumen de
    # gobernanza con lo esencial. Las filas completas están disponibles en
    # `calibration_rows` si el cliente las pide pasando `?full=1` no aplica aquí;
    # se omite por defecto para mantener la respuesta ligera.
    return {
        "schema": report["schema"],
        "dataset": report["dataset"],
        "current_params": report["current_params"],
        "selection": report["selection"],
        "review_threshold": report["review_threshold"],
        "comparison": report["comparison"],
        "evaluation": {
            "selected": report["evaluation"]["selected"],
            "current": report["evaluation"]["current"],
            "app_id_criteria": report["evaluation"]["app_id_criteria"],
        },
        "grid": report["grid"],
    }


# UI web (single-page) servida en la raíz. Se monta al final para que
# /health, /discover y /calibrate tengan precedencia sobre los estáticos.
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
