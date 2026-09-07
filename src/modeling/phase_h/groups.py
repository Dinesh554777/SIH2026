"""Phase H group definitions (A/B/C/D/E) + Phase H matrix assembly + manifest.

Group A = frozen Phase G full feature set (51 cols, identical to FREEZE_G full config).
Group B = A + temporal (th_*)
Group C = A + seasonal (sh_*)
Group D = A + event-state (es_*)
Group E = A + spatial (sp_*)
Group F = built later only if validation justifies (Step 9).

The assembly produces `phase_h_matrix.parquet` with identical row identity/order to the
training matrix, plus a deterministic feature manifest JSON.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src.modeling.common import MATRIX_PATH, PROJECT_ROOT, feature_columns
from src.modeling.phase_h import features as F

PH_OUT = PROJECT_ROOT / "data" / "processed" / "phase_h_matrix.parquet"
MANIFEST_OUT = PROJECT_ROOT / "reports" / "PHASE_H_FEATURE_MANIFEST.json"

# Group letters for the new representation groups
REP_GROUPS = ("temporal", "seasonal", "event_state", "spatial")
REP_LETTER = {"temporal": "B", "seasonal": "C", "event_state": "D", "spatial": "E"}


def _assert_row_identity(left: pd.DataFrame, right: pd.DataFrame, what: str) -> None:
    """Explicitly verify (cell_id, date) index/order match between two frames."""
    k1 = left[["cell_id", "date"]].reset_index(drop=True)
    k2 = right[["cell_id", "date"]].reset_index(drop=True)
    if not k1.equals(k2):
        raise ValueError(
            f"{what} (cell_id,date) index/order does not match the base matrix")
    if k1.duplicated().any():
        raise ValueError(f"{what} contains duplicate (cell_id,date) rows")


def build_all_groups(df: pd.DataFrame, cells: pd.DataFrame) -> dict:
    """Build every representation's new feature frame. Group A = frozen 51 predictors."""
    base = feature_columns(df)  # Group A (51 cols) from the frozen matrix

    train = df[df["split"] == "train"]

    temporal = F.build_temporal(df).drop(columns=["cell_id"])
    _assert_row_identity(pd.concat([df[["cell_id", "date"]], temporal], axis=1), df,
                         "temporal")

    cum = F.build_cum_climatology(train)

    clim_mean, clim_std, clim_pooled, onset_doy = F.build_doy_climatology(train)
    seasonal = F.seasonal_features(df, clim_mean, clim_std, clim_pooled, onset_doy)
    _assert_row_identity(pd.concat([df[["cell_id", "date"]], seasonal], axis=1), df,
                         "seasonal")

    event_state = F.event_state_features(df).drop(columns=["cell_id"])
    deficit = F.add_deficit(df, cum).drop(columns=["cell_id"])
    event_state = pd.concat([event_state, deficit], axis=1)
    _assert_row_identity(pd.concat([df[["cell_id", "date"]], event_state], axis=1),
                         df, "event_state")

    spatial = F.build_neighbor_features(df, cells).drop(columns=["cell_id"])
    _assert_row_identity(pd.concat([df[["cell_id", "date"]], spatial], axis=1), df,
                         "spatial")

    return {
        "A_group": list(base),
        "B_temporal": list(temporal.columns),
        "C_seasonal": list(seasonal.columns),
        "D_event_state": list(event_state.columns),
        "E_spatial": list(spatial.columns),
        "frames": {
            "temporal": temporal,
            "seasonal": seasonal,
            "event_state": event_state,
            "spatial": spatial,
        },
    }


def assemble_matrix(df: pd.DataFrame, res: dict) -> pd.DataFrame:
    """Join every original column + all new features into the Phase H matrix."""
    frames = res["frames"]
    out = df.copy()
    for name, frame in frames.items():
        if len(frame) != len(out):
            raise ValueError(f"{name} frame length {len(frame)} != matrix {len(out)}")
        # explicit alignment verification before positional assignment
        _assert_row_identity(pd.concat([df[["cell_id", "date"]], frame], axis=1), df,
                             name)
        key = list(frame.columns)
        for c in key:
            if c in out.columns:
                raise ValueError(f"column collision on {c}")
            out[c] = frame[c].to_numpy()
    return out


def feature_manifest(df: pd.DataFrame, res: dict) -> list[dict]:
    """Deterministic feature manifest: name, group, source, availability, train-only."""
    rows = []
    A_names = list(feature_columns(df))
    A_sources = [_group_a_source(c) for c in A_names]
    for c, src in zip(A_names, A_sources):
        rows.append({
            "feature": c, "group": "A",
            "source": src,
            "prediction_time_available": True,
            "requires_train_only_stats": bool("anom" in c),
        })
    for gname in REP_GROUPS:
        for c in res["frames"][gname].columns:
            rows.append({
                "feature": c, "group": REP_LETTER[gname],
                "source": "IMD",
                "prediction_time_available": True,
                "requires_train_only_stats": bool(
                    gname in ("seasonal", "event_state") and any(
                        k in c for k in ("z", "clim", "deficit", "pctile"))),
            })
    return rows


def _group_a_source(c: str) -> str:
    if c.startswith("imd_"):
        return "IMD"
    if c.startswith("chirps_"):
        return "CHIRPS"
    if c.startswith("nasa_"):
        return "NASA"
    if c.startswith("oni_"):
        return "ONI"
    if c in ("lat", "lon", "doy", "dseason"):
        return "CONTEXT"
    return "OTHER"


def write_manifest(rows: list[dict]) -> None:
    MANIFEST_OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"manifest: {len(rows)} features -> {MANIFEST_OUT.name}")


def run_build() -> pd.DataFrame:
    df = pd.read_parquet(MATRIX_PATH)
    cells = df[["cell_id", "lat", "lon"]].drop_duplicates()
    res = build_all_groups(df, cells)
    ph = assemble_matrix(df, res)
    ph.to_parquet(PH_OUT, index=False)
    rows = feature_manifest(df, res)
    write_manifest(rows)
    print(f"phase_h_matrix rows={len(ph)} cols={len(ph.columns)} -> {PH_OUT.name}")
    return ph
