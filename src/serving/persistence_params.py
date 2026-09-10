"""Export the frozen persistence + climatology parameters to data/serving/.

Plan gate G1 (determinism on restart): the single JSON is a machine-readable snapshot
of what serving uses, so a restart, a replay, or an external audit can verify that
on-boot values did not drift. The serving path itself still computes these from the
frozen matrix with the SAME baselines helpers; this file only mirrors them.

Run:  python -m src.serving.persistence_params
"""
from __future__ import annotations

import json

import pandas as pd

from src.modeling.baselines import build_climatology, build_persistence_transitions
from src.modeling.common import TARGETS
from src.serving import config as C
from src.serving.store import ObservationStore

_TARGETS: dict[str, str] = dict(TARGETS)


def compute_params(matrix: pd.DataFrame) -> dict:
    trans = build_persistence_transitions(matrix, _TARGETS)
    clim = build_climatology(matrix, _TARGETS)
    clim_json = {}
    for cell_id, g in clim.groupby("cell_id"):
        clim_json[cell_id] = {
            str(int(r["dseason"])): {
                t + "_clim_p": float(r[t + "_clim_p"])
                for t in ("onset", "break", "revival", "dry_spell")
            }
            for _, r in g.iterrows()
        }
    return {
        "schema_version": 1,
        "description": (
            "Persistence P(y_t|y_{t-1}) + cell-dseason climatology probabilities, "
            "estimated on TRAIN (2015-2021) only. Mirrors serving-on-boot values "
            "produced by build_persistence_transitions/build_climatology."
        ),
        "freeze_digest": "see data/processed/FREEZE_H.json at serve time",
        "fit_split": "train",
        "persistence_transitions": {
            k: {"p11": v["p11"], "p01": v["p01"]} for k, v in trans.items()
        },
        "climatology": {
            "n_cell_dseason_combos": int(len(clim)),
            "by_cell": clim_json,
        },
    }


def export_params(path=None) -> None:
    from pathlib import Path

    store = ObservationStore.from_file()
    params = compute_params(store.matrix)
    out = Path(path) if path else (C.SERVING_DIR / "persistence_params.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(params, indent=2), encoding="utf-8")
    print(f"wrote {out}  ({len(params['climatology']['by_cell'])} cells)")


if __name__ == "__main__":
    export_params()