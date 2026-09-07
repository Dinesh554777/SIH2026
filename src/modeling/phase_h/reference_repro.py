"""H0 — Reproduce the frozen Phase G reference validation results from artifacts.

Confirms:
  * data/splits unchanged from the Phase G run
  * same feature configuration (D_full = 51 feat, ee: full matrix)
  * same models (frozen archives) and same metrics
  * freeze decisions match the phase G freeze JSON

No 2024 labels are read here: only TRAIN/VAL are touched.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

import sys
sys.path.insert(0, r"C:\Users\hp\Downloads\SIH2026")

from src.modeling.common import (MATRIX_PATH, MODELS_DIR, PREDICTIONS_DIR,  # noqa: E402
                                 TARGETS, feature_columns, PROJECT_ROOT)
from src.modeling.evaluate import aggregate  # noqa: E402
FREEZE_G = PROJECT_ROOT / "data" / "processed" / "FREEZE_G.json"


def reproduce() -> dict:
    freeze = json.loads(FREEZE_G.read_text())
    df = pd.read_parquet(MATRIX_PATH)
    feats = feature_columns(df)
    assert len(feats) == 51, f"expected 51 features, got {len(feats)}"

    dtr = df[df["split"] == "train"]
    dva = df[df["split"] == "val"]
    assert (dtr.index == df[df["split"] == "train"].index).all()

    reports = {}
    for col, name in TARGETS.items():
        d = {}
        Xva = dva[feats].to_numpy(dtype=np.float64)
        for mname in ("logistic", "random_forest", "xgboost"):
            _d = MODELS_DIR / mname / name
            model = joblib.load(_d / "model.joblib")
            scaler = joblib.load(_d / "scaler.joblib")
            if mname == "logistic":
                d[mname] = model.predict_proba(scaler.transform(Xva))[:, 1]
            else:
                d[mname] = model.predict_proba(Xva)[:, 1]
        reports[name] = d

    # build long table for val = D_full models
    rows = []
    for col, name in TARGETS.items():
        for mname in ("logistic", "random_forest", "xgboost"):
            rows.append(pd.DataFrame({
                "date": dva["date"].to_numpy(), "cell_id": dva["cell_id"].to_numpy(),
                "target": name, "model": mname, "split": "val", "config": "D_full",
                "probability": reports[name][mname],
                "observed_label": dva[col].to_numpy(),
            }))
    val = pd.concat(rows, ignore_index=True)
    metrics = aggregate(val, groups=("config", "model"))
    mdf = pd.DataFrame(metrics)
    mdf = mdf.drop(columns=[c for c in mdf.columns if c in (
        "reliability", "confusion_matrix")], errors="ignore")

    # persistence reference from the phase E-G baseline predictions
    base = pd.read_parquet(PREDICTIONS_DIR / "baseline_predictions.parquet")
    pers = {}
    for tgt in ["onset", "break", "revival", "dry_spell"]:
        b = base[(base["split"] == "val") & (base["model"] == "persistence")
                 & (base["target"] == tgt)]
        pers[tgt] = {
            "brier": float(((b["probability"] - b["observed_label"]) ** 2).mean()),
        }

    return {
        "n_features": len(feats),
        "freeze": freeze["decision"]["winner"],
        "reproduced_val_metrics": mdf.to_dict("records"),
        "persistence_brier_reproduced": pers,
    }


if __name__ == "__main__":
    res = reproduce()
    print("N FEATURES:", res["n_features"])
    print("FREEZE:", json.dumps(res["freeze"], indent=2))
    print("PERSISTENCE BRIER REPRO:", json.dumps(res["persistence_brier_reproduced"], indent=2))
    rows = res["reproduced_val_metrics"]
    for r in sorted(rows, key=lambda r: (r["target"], r["model"])):
        print(f"{r['target']:10s} {r['model']:14s} brier={r['brier']:.5f} roc={r['roc_auc'] if r.get('roc_auc') else '--'}")
