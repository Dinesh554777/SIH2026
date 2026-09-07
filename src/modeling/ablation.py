"""Phase G feature ablation.

Canonical configuration ladder (all share lat/lon/doy/dseason context):
  A: IMD only                      (28 cols)
  B: A + CHIRPS                    (33)
  C: B + ONI                       (35)
  D: C + NASA = full E/F matrix    (51)

All models fitted on TRAIN (2015-2021) only, identical hyperparameters to Phases E-F.
Config D reuses the Phase E-F artifacts (identical model config + feature set), avoiding
a redundant refit. Predictions are saved under data/processed/predictions/ablation/
so the run is resumable.
"""
from __future__ import annotations

import joblib
import pandas as pd

from src.modeling.common import (MATRIX_PATH, MODELS_DIR, PREDICTIONS_DIR, TARGETS,
                                 feature_columns)
from src.modeling.train_ml import predict_row_arrays, train_target

ABLATION_DIR = PREDICTIONS_DIR / "ablation"
ML_MODELS = ["logistic", "random_forest", "xgboost"]


def make_configs(df: pd.DataFrame) -> dict[str, list[str]]:
    feats = feature_columns(df)
    def keep(prefixes):
        return [c for c in feats if any(c.startswith(p) for p in prefixes)]

    imd = keep(("imd_",))
    chirps = keep(("chirps_",))
    oni = keep(("oni_",))
    nasa = keep(("nasa_",))
    context = [c for c in ("lat", "lon", "doy", "dseason") if c in feats]

    return {
        "A_imd": imd + context,
        "B_imd_chirps": imd + chirps + context,
        "C_imd_chirps_oni": imd + chirps + oni + context,
        "D_full": feats,
    }


def run_ablation(df: pd.DataFrame, configs: dict[str, list[str]]) -> None:
    """Fit logistic/RF/XGB per (target, config) on train; save train+val predictions. Resumable."""
    ABLATION_DIR.mkdir(parents=True, exist_ok=True)
    dtr = df[df["split"] == "train"]
    dva = df[df["split"] == "val"]
    for cfg_name, cfg_feats in configs.items():
        if cfg_name == "D_full":
            continue
        out_path = ABLATION_DIR / f"{cfg_name}.parquet"
        if out_path.exists():
            print(f"[ablation] skip {cfg_name} (predictions exist)")
            continue
        rows = []
        for col, name in TARGETS.items():
            models, scaler, cfgmeta = train_target(dtr, dva, cfg_feats, name, col)
            # save artifacts under models/ablation/<config>/<target>/<model>
            for mname, model in models.items():
                d = MODELS_DIR / "ablation" / cfg_name / name / mname
                d.mkdir(parents=True, exist_ok=True)
                joblib.dump(model, d / "model.joblib")
                if mname == "logistic":
                    joblib.dump(scaler, d / "scaler.joblib")
            for split_label, d in (("train", dtr), ("val", dva)):
                probs = predict_row_arrays(models, d, cfg_feats, scaler)
                for mname, p in probs.items():
                    rows.append(pd.DataFrame({
                        "date": d["date"].to_numpy(), "cell_id": d["cell_id"].to_numpy(),
                        "target": name, "model": mname, "split": split_label,
                        "probability": p, "observed_label": d[col].to_numpy(),
                        "config": cfg_name,
                    }))
            print(f"[ablation] {cfg_name} -> {name}")
        pd.concat(rows, ignore_index=True).to_parquet(out_path, index=False)
        print(f"[ablation] saved {out_path.name}")


def load_ablation_predictions(configs: dict[str, list[str]]) -> pd.DataFrame:
    parts = []
    for cfg_name in configs:
        if cfg_name == "D_full":
            p = PREDICTIONS_DIR / "ml_train_val_predictions.parquet"
            d = pd.read_parquet(p)
            d = d[d["split"].isin(["train", "val"])]
            d["config"] = "D_full"
            parts.append(d)
            continue
        f = ABLATION_DIR / f"{cfg_name}.parquet"
        if f.exists():
            parts.append(pd.read_parquet(f))
        else:
            print(f"[warn] missing ablation predictions: {f.name}")
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()