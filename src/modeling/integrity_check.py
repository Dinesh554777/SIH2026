"""Pre-training integrity check (Prompt §7). Must pass or STOP (fail loudly)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data_pipeline_utils import PROCESSED  # noqa: E402

TARGETS = ["onset_active", "break_active", "dry_spell_active", "revival_day"]
META = ["cell_id", "date", "year", "doy", "dseason", "insufficient_data",
        "onset_date", "bbox_guess", "admin_mapping", "split", "lat", "lon"]
FEATURE_STEMS = ("imd_", "chirps_", "nasa_", "oni_")


def run_integrity_check(path=PROCESSED / "training_matrix.parquet") -> dict:
    m = pd.read_parquet(path)
    issues = []

    feats = [c for c in m.columns if c.startswith(FEATURE_STEMS) or c in ("lat", "lon", "doy", "dseason")]
    for t in TARGETS:
        if t not in m.columns:
            issues.append(f"missing target {t}")
    if m["cell_id"].nunique() != 304:
        issues.append("expected 304 cells")
    if m.duplicated(subset=["cell_id", "date"]).any():
        issues.append("duplicate (cell_id,date)")
    if m[feats].isna().sum().sum():
        issues.append("NaN in features")
    inf = np.isinf(m[feats].to_numpy()).sum()
    if inf:
        issues.append(f"{inf} infinite values in features")
    for t in TARGETS:
        if not m[t].isin([0, 1]).all():
            issues.append(f"target {t} not binary")
    spans = m.groupby("split")["year"].agg(["min", "max"])
    if not (spans.loc["train", "max"] <= 2021 and spans.loc["train", "min"] >= 2015):
        issues.append("train outside 2015-2021")
    if not (spans.loc["val", "min"] >= 2022 and spans.loc["val", "max"] <= 2023):
        issues.append("val outside 2022-2023")
    if not (spans.loc["test", "min"] == 2024 and spans.loc["test", "max"] == 2024):
        issues.append("test outside 2024")
    # chronological: date strictly increasing within each cell
    dates = pd.to_datetime(m["date"])
    mono = m.assign(d=dates).groupby("cell_id")["d"].is_monotonic_increasing.all()
    if not mono:
        issues.append("dates not monotonic within cells")
    # no cell drain across splits
    cells_train = set(m.loc[m.split == "train", "cell_id"])
    cells_val = set(m.loc[m.split == "val", "cell_id"])
    cells_test = set(m.loc[m.split == "test", "cell_id"])
    if not (cells_train == cells_val == cells_test):
        issues.append("cell sets differ across splits")
    # feature-count sanity
    if len(feats) < 40:
        issues.append(f"unexpectedly few features ({len(feats)})")

    return {
        "path": str(path),
        "rows": len(m),
        "columns": len(m.columns),
        "n_feature_cols": len(feats),
        "n_cells": m["cell_id"].nunique(),
        "n_targets": len([t for t in TARGETS if t in m.columns]),
        "issues": issues,
    }


if __name__ == "__main__":
    res = run_integrity_check()
    print(res)
    if res["issues"]:
        print("INTEGRITY CHECK FAILED — STOP")
        raise SystemExit(1)
    print("INTEGRITY CHECK PASSED")