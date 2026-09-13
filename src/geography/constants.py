"""Geography / agricultural pilot constants (single source of truth).

The scientific layer (0.25-degree grid cells, frozen Phase H model) is untouched.
Administrative geography is a PRODUCT/DECISION layer populated ONLY from
authoritative GIS boundary sources registered under `data/geography/sources/`.
Without a registered authoritative source for a level, that level stays
`unavailable` -- boundaries are never invented.
"""
from __future__ import annotations

from pathlib import Path

from src.data_pipeline_utils import ROOT as PROJECT_ROOT

# Administrative hierarchy (product layer). Grid cells are NOT administrative.
GEOGRAPHY_TYPES = ("state", "district", "block", "village")

# geography_type -> parent geography_type
HIERARCHY = {"district": "state", "block": "district", "village": "block"}

GRID_CELL_TYPE = "grid_cell"

# Availability semantics: an empty result is `unavailable`, never a fabricated
# inventory. `unknown` means the level is structurally configured.
AVAILABLE = "available"
UNAVAILABLE = "unavailable"

# Deterministic mapping methods (only area-weighted intersection is used for
# authoritative boundaries; centroid-only exists for explicitly-justified use).
AREA_WEIGHTED = "area_weighted_intersection"
CENTROID_ONLY = "centroid_only"

# Grid geometry (mm/dd constants mirror the scientific grid; DO NOT change).
GRID_STEP_DEG = 0.25

# Directory where authoritative GIS sources may be dropped.
# Format: one folder per source, containing `source.json` (mandatory metadata)
# plus one or more GeoJSON files whose features carry properties
# {level, id, name, parent_id}. Source folders are never auto-imported without
# a valid source.json (no silent boundary ingestion).
GEOGRAPHY_SOURCES_DIR = PROJECT_ROOT / "data" / "geography" / "sources"
GEOGRAPHY_AGRI_DIR = PROJECT_ROOT / "data" / "geography" / "agriculture"
GEOGRAPHY_READY_DIR = PROJECT_ROOT / "data" / "geography" / "ready"
SOURCE_META_FILE = "source.json"

# Agricultural metadata field contract (authoritative values only).
AGRI_METADATA_FIELDS = (
    "major_crop",          # e.g. paddy (rice) for the Cauvery delta
    "cropping_season",     # e.g. kharif monsoon cropping window
    "irrigation_dependence",
    "agricultural_zone",
    "monsoon_relevance",
    "sowing_window",
    "drought_sensitivity",
)