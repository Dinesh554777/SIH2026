"""Phase C: assemble the chronological training matrix (leakage-safe by design).

Pipeline: raw IMD -> pilot cells (304) -> labels (Phase A) -> features (Phase B)
-> single long matrix with a calendar-based split column.

Split (NEVER shuffled):
    train  2015-01-01 .. 2021-12-31   (climatology fit windows)
    val    2022-01-01 .. 2023-12-31
    test   2024-01-01 .. 2024-12-31

Samples are JJAS days only (the onset/break/dry-spell label targets are defined
in that window). CHIRPS cell series is cached under data/processed/cache.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.data_pipeline_utils import PROCESSED  # noqa: E402
from src.features.build_features import (  # noqa: E402
    build_feature_matrix, CACHE)


def load_chirps_cached(cells: pd.DataFrame) -> pd.DataFrame:
    p = CACHE / "chirps_cells.parquet"
    if p.exists():
        df = pd.read_parquet(p)
        df = df[df["cell_id"].isin(cells["cell_id"])]
        if len(df):
            return df
    from src import load
    df = load.chirps_cell_series(cells)
    df.to_parquet(p)
    return df


def make_matrix() -> pd.DataFrame:
    from src import load
    from src.labels.build_labels import build_label_tables

    imd = load.imd_series()
    cells = load.select_pilot_cells(imd)
    imd["year"] = pd.to_datetime(imd["date"]).dt.year
    imd = imd[imd["cell_id"].isin(cells["cell_id"])]
    daily, events = build_label_tables(imd, cells)
    chirps = load_chirps_cached(cells)
    m = build_feature_matrix(imd[["cell_id", "lat", "lon", "date", "rain", "valid"]],
                             cells, daily, chirps=chirps)

    d = pd.to_datetime(m["date"])
    m["split"] = np.select(
        [d <= pd.Timestamp("2021-12-31"), d <= pd.Timestamp("2023-12-31")],
        ["train", "val"], default="test")
    return m


if __name__ == "__main__":
    m = make_matrix()
    out = PROCESSED / "training_matrix.parquet"
    m.to_parquet(out)
    print("saved", out, "rows", len(m), "cols", len(m.columns))
    tg = ["onset_active", "break_active", "dry_spell_active", "revival_day"]
    print(m.groupby("split")[tg].agg(["mean", "count"]).round(4).to_string())
    feats = [c for c in m.columns if c not in
        ["cell_id", "lat", "lon", "bbox_guess", "admin_mapping", "date", "year",
         "doy", "dseason", "split", "insufficient_data", "onset_date"]
        + tg]
    print("numeric feature count:", len(feats))
    print("NaN cells in features:", int(m[feats].isna().sum().sum()))