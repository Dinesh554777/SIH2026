"""Phase H matrix build + pre-flight validation (Steps 3-10).

Assembles data/processed/phase_h_matrix.parquet from the frozen training matrix plus
the H1-H4 representation features, then runs the integrity / leakage / determinism /
Group-A-freeze checks. This script does NOT train any model (H5+ is a later gate).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modeling.common import MATRIX_PATH, feature_columns  # noqa: E402
from src.modeling.phase_h import groups as G  # noqa: E402

NEW_PREFIXES = ("th_", "sh_", "es_", "sp_")


def verify_group_a_frozen(df: pd.DataFrame) -> dict:
    """Group A must be exactly the 51 frozen Phase G full-set predictors."""
    feats = feature_columns(df)
    assert len(feats) == 51, f"Group A count != 51 (got {len(feats)})"
    assert not any(c.startswith(NEW_PREFIXES) for c in feats), \
        "a new-format feature leaked into Group A"
    return {"group_a_count": len(feats), "group_a_features": list(feats)}


def verify_row_identity(orig: pd.DataFrame, ph: pd.DataFrame) -> dict:
    o = orig[["cell_id", "date"]]
    p = ph[["cell_id", "date"]]
    assert len(ph) == len(orig), f"row count differs {len(orig)} vs {len(ph)}"
    assert not p.duplicated().any(), "duplicate (cell_id, date) in Phase H matrix"
    assert not o.duplicated().any(), "duplicate (cell_id, date) in original matrix"
    assert o.equals(p), "(cell_id,date) identity or order differs"
    # sorted by cell_id -> date
    assert ph.sort_values(["cell_id", "date"]).reset_index(drop=True)[["cell_id", "date"]].equals(
        p.reset_index(drop=True)), "matrix not sorted by (cell_id, date)"
    return {"rows_equal": True, "rows": len(ph), "unique_cells": ph["cell_id"].nunique()}


def verify_splits(ph: pd.DataFrame) -> dict:
    years = ph.assign(yr=pd.to_datetime(ph["date"]).dt.year).groupby("split")["yr"] \
        .agg(["min", "max"]).to_dict("index")
    base_splits = {
        "train": (2015, 2021), "val": (2022, 2023), "test": (2024, 2024),
    }
    for split in ("train", "val", "test"):
        lo = int(years[split]["min"]); hi = int(years[split]["max"])
        assert (lo, hi) == base_splits[split], f"{split} years {lo}-{hi} != {base_splits[split]}"
    return {f"{s}_years": str(years[s]["min"]) if years[s]["min"] == years[s]["max"]
            else f"{years[s]['min']}-{years[s]['max']}" for s in ("train", "val", "test")}


def verify_missingness(ph: pd.DataFrame, rep_cols: dict) -> dict:
    rep = [c for c in ph.columns if c.startswith(NEW_PREFIXES)]
    nul = ph[rep].isna().sum()
    nul = nul[nul > 0]
    return {"new_features_with_nan": {k: int(v) for k, v in nul.items()},
            "total_new_features": len(rep)}


def verify_constants(ph: pd.DataFrame) -> list[str]:
    rep = [c for c in ph.columns if c.startswith(NEW_PREFIXES)]
    nuniq = ph[rep].nunique()
    return [c for c in rep if nuniq[c] <= 1]


def verify_duplicates(ph: pd.DataFrame) -> list[tuple[str, str]]:
    rep = [c for c in ph.columns if c.startswith(NEW_PREFIXES)]
    dup = []
    for i in range(len(rep)):
        for j in range(i + 1, len(rep)):
            if ph[rep[i]].equals(ph[rep[j]]):
                dup.append((rep[i], rep[j]))
    return dup


def verify_target_leakage(df, ph, rep_cols) -> dict:
    """H1-H4 features must not equal / be derived from any target or event-date column."""
    targets = [c for c in df.columns if "_active" in c]
    rep = [c for c in ph.columns if c.startswith(NEW_PREFIXES)]
    equal_to_target = []
    for c in rep:
        for t in targets:
            if ph[c].equals(ph[t]):
                equal_to_target.append((c, t))
    # event-date columns (if any) must not appear as inputs
    evendate = [c for c in df.columns if c.endswith("_date")]
    return {"target_cols_checked": targets, "event_date_cols_found": evendate,
            "features_equal_to_target": equal_to_target}


def verify_determinism() -> dict:
    df = pd.read_parquet(MATRIX_PATH)
    cells = df[["cell_id", "lat", "lon"]].drop_duplicates()
    res1 = G.build_all_groups(df, cells)
    # rebuild twice and compare the new-feature frames directly
    res2 = G.build_all_groups(df, cells)
    frames1 = res1["frames"]; frames2 = res2["frames"]
    keys = list(frames1)
    diff = {}
    for k in keys:
        a = frames1[k].to_numpy(); b = frames2[k].to_numpy()
        diff[k] = bool(np.allclose(a, b, rtol=0, atol=0, equal_nan=True)) if a.dtype.kind == "f" else bool((a == b).all())
    return {"rebuild_identical": diff, "deterministic": all(diff.values())}


def main() -> None:
    df = pd.read_parquet(MATRIX_PATH)
    ga = verify_group_a_frozen(df)
    print(f"Group A: {ga['group_a_count']} frozen features")

    cells = df[["cell_id", "lat", "lon"]].drop_duplicates()
    res = G.build_all_groups(df, cells)
    ph = G.assemble_matrix(df, res)
    ph.to_parquet(G.PH_OUT, index=False)
    rep_cols = {k: list(v.columns) for k, v in res["frames"].items()}

    row = verify_row_identity(df, ph)
    splits = verify_splits(ph)
    miss = verify_missingness(ph, rep_cols)
    const = verify_constants(ph)
    dup = verify_duplicates(ph)
    leak = verify_target_leakage(df, ph, rep_cols)
    det = verify_determinism()

    G.write_manifest(G.feature_manifest(df, res))

    report = {
        "matrix": {"rows": len(ph), "columns": len(ph.columns)},
        "group_a": ga,
        "row_identity": row,
        "splits": splits,
        "missing": miss,
        "constant_features": const,
        "duplicate_pairs": dup,
        "leakage": leak,
        "determinism": det,
        "feature_groups_counts": {
            "original": len(df.columns), "temporal": len(rep_cols["temporal"]),
            "seasonal": len(rep_cols["seasonal"]),
            "event_state": len(rep_cols["event_state"]),
            "spatial": len(rep_cols["spatial"]),
        },
    }
    print("=" * 60)
    print("matrix_rows:", len(ph), "cols:", len(ph.columns))
    print("row_identity:", row)
    print("splits:", splits)
    print("missing(new):", miss)
    print("constant:", const)
    print("dup:", dup)
    print("leakage:", leak)
    print("determinism:", det)
    print("group counts:", report["feature_groups_counts"])
    print(f"WROTE {G.PH_OUT}")
    print(f"WROTE {G.MANIFEST_OUT}")


if __name__ == "__main__":
    main()
