"""Shared constants, feature lists, paths, seeds for Phases E-F."""
from __future__ import annotations

import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data_pipeline_utils import PROCESSED, ROOT as PROJECT_ROOT  # noqa: E402

RANDOM_SEED = 42

MATRIX_PATH = PROCESSED / "training_matrix.parquet"
PREDICTIONS_DIR = PROCESSED / "predictions"
MODELS_DIR = PROJECT_ROOT / "models"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
FREEZE_PATH = PROCESSED / "FREEZE.json"
MANIFEST_PATH = PROJECT_ROOT / "reports" / "MODELING_RUN_MANIFEST.json"

# Target column -> public target name
TARGETS = {
    "onset_active": "onset",
    "break_active": "break",
    "revival_day": "revival",
    "dry_spell_active": "dry_spell",
}
PUBLIC_TARGETS = list(TARGETS.values())

MODELS = ["climatology", "persistence", "logistic", "random_forest", "xgboost"]

FEATURE_STEMS = ("imd_", "chirps_", "nasa_", "oni_")
CONTEXT_FEATS = ("lat", "lon", "doy", "dseason")


def feature_columns(matrix: pd.DataFrame) -> list[str]:
    return [c for c in matrix.columns
            if c.startswith(FEATURE_STEMS) or c in CONTEXT_FEATS]


def region_of(bbox_guess: str) -> str:
    """Crude regional grouping. ADMIN NOT AUTHORITATIVE (bbox_guess only)."""
    if bbox_guess == "MH":
        return "MH"
    return "KA" if bbox_guess in ("TN;KA", "KA") else "TN"


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mkdirs() -> None:
    for d in (PREDICTIONS_DIR, FIGURES_DIR):
        d.mkdir(parents=True, exist_ok=True)
    for mname in MODELS:
        (MODELS_DIR / mname).mkdir(parents=True, exist_ok=True)


def write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def pkg_versions() -> dict:
    import importlib
    out = {}
    for name in ("numpy", "pandas", "sklearn", "xgboost", "matplotlib", "pyarrow"):
        try:
            out[name] = importlib.import_module(name).__version__
        except Exception:
            out[name] = "n/a"
    out["python"] = platform.python_version()
    return out