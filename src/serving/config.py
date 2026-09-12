"""Serving configuration: canonical paths to frozen artifacts.

Environment overrides (optional, keep defaults for the hackathon):
- SIH_PROJECT_ROOT : project root directory
- MODEL_DIR or SIH_MODELS_ROOT : directory containing the `models` folder
- DATA_DIR or SIH_DATA_ROOT   : directory containing the `data` folder

Backend environment (Phase I-A foundation):
- ENVIRONMENT   : development | test | production  (default development)
- GROQ_API_KEY  : empty placeholder until the Groq phase (never commit a real key)
- DATABASE_URL  : consumed by src.database.config (PostgreSQL phase), not here.

All artifact paths below point at EXISTING frozen files; serving never writes
into the models/ or data/processed trees.
"""
from __future__ import annotations

import os
from pathlib import Path

from src.data_pipeline_utils import ROOT as _PROJECT_ROOT

PROJECT_ROOT = Path(os.environ.get("SIH_PROJECT_ROOT", _PROJECT_ROOT))

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")  # placeholder only until the Groq phase

MODELS_ROOT = Path(os.environ.get("MODEL_DIR") or os.environ.get("SIH_MODELS_ROOT")
                   or PROJECT_ROOT / "models")
DATA_ROOT = Path(os.environ.get("DATA_DIR") or os.environ.get("SIH_DATA_ROOT")
                 or PROJECT_ROOT / "data")

PROCESSED = DATA_ROOT / "processed"
MODELS = MODELS_ROOT

PH_MATRIX = PROCESSED / "phase_h_matrix.parquet"
FREEZE_H = PROCESSED / "FREEZE_H.json"
SERVING_DIR = PROJECT_ROOT / "data" / "serving"

REVIVAL_DIR = MODELS / "phase_h" / "B" / "revival"

# Frozen architecture per FREEZE_H.json (do not change).
TARGETS = ("onset", "break", "revival", "dry_spell")
REVIVAL_TARGET = "revival"
PERSISTENCE_TARGETS = ("onset", "break", "dry_spell")
REVIVAL_MODEL_FILES = ("xgboost.joblib", "imputer.joblib", "CONFIG.json")

# Onset/break/dry-spell use persistence. Revival uses XGBoost + Group B (64 feats).
MODEL_SPEC = {
    "onset": "persistence",
    "break": "persistence",
    "dry_spell": "persistence",
    "revival": "xgboost_groupB",
}

DATA_MODE = "historical/demo"  # no live feed in the MVP; UI must state this
SPATIAL_UNIT = {
    "type": "regular_grid_0.25deg",
    "step_degrees": 0.25,
    "approx_km": "~25 x 25",
    "note": "Pilot grid cell. Not an official village/block boundary.",
    "pilot_regions": ["TN", "MH", "KA"],
}

FORECAST_HORIZON_NOTE = (
    "Forecast is generated AFTER the day's rainfall observations are available "
    "(same-day IMD grid + neighbouring cells). Probabilities describe whether each "
    "monsoon target state is active on the observation date."
)