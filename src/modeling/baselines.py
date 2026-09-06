"""E0 Climatology and E1 Persistence baselines (Phase E).

Climatology : empirical event probability per (cell, dseason) estimated on TRAIN ONLY.
Persistence : two-state Markov transition probabilities P(y_t | y_{t-1}) estimated on
TRAIN ONLY; first JJAS day of each season falls back to cell-dseason climatology.

Both produce probabilities for TRAIN, VALIDATION and TEST by pure table lookup.
Nothing here is fitted on validation or test labels.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.modeling.common import MATRIX_PATH, TARGETS, feature_columns


def build_climatology(matrix: pd.DataFrame, targets: dict[str, str]) -> pd.DataFrame:
    train = matrix[matrix["split"] == "train"]
    key = ["cell_id", "dseason"]
    rows = []
    for col, name in targets.items():
        g = train.groupby(key)[col].mean().rename(name + "_clim_p").reset_index()
        rows.append(g)
    clim = rows[0]
    for r in rows[1:]:
        clim = clim.merge(r, on=key, how="outer")
    return clim


def build_persistence_transitions(matrix: pd.DataFrame, targets: dict[str, str]) -> dict:
    train = matrix[matrix["split"] == "train"].sort_values(["cell_id", "date"])
    out = {}
    for col, name in targets.items():
        prev = train.groupby("cell_id")[col].shift(1)
        valid = train.index[train["dseason"] > 1]
        y = train.loc[valid, col].to_numpy()
        p = prev.loc[valid].to_numpy()
        mask_prev1 = p == 1
        mask_prev0 = p == 0
        p11 = float(y[mask_prev1].mean()) if mask_prev1.any() else float("nan")
        p01 = float(y[mask_prev0].mean()) if mask_prev0.any() else float("nan")
        out[name] = {"p11": p11, "p01": p01}
        print(f"[persistence] {name}: P(y=1|prev=1)={p11:.4f}  P(y=1|prev=0)={p01:.4f}")
    return out


def baseline_predictions(matrix: pd.DataFrame, clim: pd.DataFrame,
                         trans: dict, targets: dict[str, str]) -> pd.DataFrame:
    """Return long prediction table: date, cell_id, target, model, split, probability, observed_label."""
    matrix = matrix.sort_values(["cell_id", "date"]).reset_index(drop=True)
    key = ["cell_id", "dseason"]
    rows = []
    tmp = matrix.merge(clim, on=key, how="left")
    for col, name in targets.items():
        # --- climatology ---
        p_clim = tmp[name + "_clim_p"]
        df_clim = pd.DataFrame({
            "date": matrix["date"], "cell_id": matrix["cell_id"],
            "target": name, "model": "climatology", "split": matrix["split"],
            "probability": p_clim.to_numpy(), "observed_label": matrix[col].to_numpy(),
        })
        # --- persistence ---
        prev_label = matrix.groupby("cell_id")[col].shift(1)
        p_per = prev_label.map({1: trans[name]["p11"], 0: trans[name]["p01"]}).astype(float)
        d1 = matrix["dseason"] == 1
        p_per.loc[d1] = p_clim.loc[d1]
        df_per = pd.DataFrame({
            "date": matrix["date"], "cell_id": matrix["cell_id"],
            "target": name, "model": "persistence", "split": matrix["split"],
            "probability": p_per.to_numpy(), "observed_label": matrix[col].to_numpy(),
        })
        rows.append(df_clim)
        rows.append(df_per)
    return pd.concat(rows, ignore_index=True)


def write_baseline_metadata(clim: pd.DataFrame, trans: dict) -> dict:
    return {
        "description": "E0 climatology: P(target|cell, dseason) empirical mean on TRAIN (2015-2021). "
                       "E1 persistence: two-state Markov P(y_t|y_{t-1}) from TRAIN; dseason==1 uses climatology.",
        "climatology": {"n_cell_dseason_combos": int(len(clim)),
                        "fit_split": "train"},
        "persistence_transitions": {k: {"p11": v["p11"], "p01": v["p01"]} for k, v in trans.items()},
    }