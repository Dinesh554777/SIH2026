"""Idempotent database seeding (Phase I-B).

Run:  python -m src.database.seed
Depends on DATABASE_URL being configured (.env). Seeds:
  1. `cells`          - 304 pilot grid cells, derived fresh from the Phase H matrix
                        via the serving CellRegistry (authoritative; nothing hand-typed).
  2. `model_metadata` - frozen model provenance from FREEZE_H.json (4 rows, one per target).

Safe to re-run any number of times (ON CONFLICT DO NOTHING).
"""
from __future__ import annotations

import json

import pandas as pd

from src.data_pipeline_utils import ROOT
from src.database import config
from src.database.db import connect
from src.database.models import Cell, ModelMetadata
from src.database.repository import (count_rows, seed_cells,
                                     seed_model_metadata)
from src.serving.config import FREEZE_H
from src.serving.models import freeze_digest
from src.serving.registry import default_registry


def load_cells() -> pd.DataFrame:
    matrix = pd.read_parquet(ROOT / "data" / "processed" / "phase_h_matrix.parquet")
    return default_registry(matrix).cells


def load_freeze() -> tuple[dict, str]:
    return json.load(open(FREEZE_H, encoding="utf-8")), freeze_digest()


def seed(session, cells: pd.DataFrame, freeze: dict, digest: str) -> dict:
    n_cells = seed_cells(session, cells)
    n_versions = seed_model_metadata(session, freeze, digest)
    return {
        "cells_seeded": n_cells,
        "model_metadata_rows": n_versions,
        "cells_total": count_rows(session, Cell),
        "model_metadata_total": count_rows(session, ModelMetadata),
    }


def main() -> None:
    if not config.database_url():
        raise SystemExit(
            "DATABASE_URL not set. Copy .env.example to .env and fill in the DSN first.")
    cells = load_cells()
    freeze, digest = load_freeze()
    with connect() as session:
        result = seed(session, cells, freeze, digest)
    print(f"Seeded {result['cells_seeded']} of 304 cells "
          f"(table now has {result['cells_total']}); "
          f"model_metadata table now has {result['model_metadata_total']} rows "
          f"(4 frozen targets) for digest {digest}.")


if __name__ == "__main__":
    main()