"""Phase E2-E4: Logistic Regression, Random Forest, XGBoost.

All models are fitted on TRAIN (2015-2021) only. Predictions are produced for TRAIN and
VALIDATION now; TEST predictions are deliberately deferred and gated by the freeze file.
Preprocessing (StandardScaler for logistic) is fitted on TRAIN only.
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.modeling.common import MATRIX_PATH, MODELS_DIR, PREDICTIONS_DIR, TARGETS, \
    RANDOM_SEED, feature_columns, pkg_versions, utcnow, write_json

ML_MODELS = ["logistic", "random_forest", "xgboost"]


def train_target(df_train, df_val, feats, name: str, col: str) -> tuple:
    """Fit all three ML models for one target; return (models, scaler)."""
    Xtr = df_train[feats].to_numpy(dtype=np.float64)
    Xva = df_val[feats].to_numpy(dtype=np.float64)
    ytr = df_train[col].to_numpy(dtype=np.float64)
    yva = df_val[col].to_numpy(dtype=np.float64)
    pos = int(ytr.sum()); neg = int(len(ytr) - pos)

    models = {}

    # ---- E2 Logistic Regression (scaled on train only) ----
    scaler = StandardScaler().fit(Xtr)
    lr = LogisticRegression(
        C=1.0, class_weight="balanced", solver="lbfgs",
        max_iter=2000, random_state=RANDOM_SEED)
    lr.fit(scaler.transform(Xtr), ytr)
    models["logistic"] = lr

    # ---- E3 Random Forest (no scaling; balanced for train imbalance) ----
    rf = RandomForestClassifier(
        n_estimators=250, max_depth=14, min_samples_leaf=20,
        class_weight="balanced", n_jobs=-1, random_state=RANDOM_SEED)
    rf.fit(Xtr, ytr)
    models["random_forest"] = rf

    # ---- E4 XGBoost (conservative params; scale_pos_weight from train imbalance) ----
    xg = xgb.XGBClassifier(
        n_estimators=300, max_depth=6, learning_rate=0.1,
        subsample=0.9, colsample_bytree=0.9,
        scale_pos_weight=neg / max(pos, 1),
        tree_method="hist", n_jobs=-1, random_state=RANDOM_SEED,
        eval_metric="logloss")
    xg.fit(Xtr, ytr)
    models["xgboost"] = xg

    cfg = {
        "target": name,
        "features": feats,
        "n_train": int(len(Xtr)),
        "n_val": int(len(Xva)),
        "n_pos_train": pos,
        "n_neg_train": neg,
        "logistic": {"C": 1.0, "class_weight": "balanced", "solver": "lbfgs", "scaling": "StandardScaler fit on train"},
        "random_forest": {"n_estimators": 250, "max_depth": 14, "min_samples_leaf": 20, "class_weight": "balanced"},
        "xgboost": {"n_estimators": 300, "max_depth": 6, "learning_rate": 0.1,
                    "subsample": 0.9, "colsample_bytree": 0.9,
                    "scale_pos_weight": round(neg / max(pos, 1), 3), "tree_method": "hist"},
        "seed": RANDOM_SEED,
        "fit_split": "train (2015-2021)",
        "trained_at": utcnow(),
        "versions": pkg_versions(),
    }
    return models, scaler, cfg


def predict_row_arrays(models: dict, df, feats, scaler=None) -> dict[str, np.ndarray]:
    X = df[feats].to_numpy(dtype=np.float64)
    out = {}
    for name, m in models.items():
        if name == "logistic":
            out[name] = m.predict_proba(scaler.transform(X))[:, 1]
        else:
            out[name] = m.predict_proba(X)[:, 1]
    return out


def save_models_artifacts(models: dict, scaler, cfg: dict, name: str) -> None:
    for mname, model in models.items():
        d = MODELS_DIR / mname / name
        d.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, d / "model.joblib")
        joblib.dump(scaler, MODELS_DIR / mname / name / "scaler.joblib")
    write_json(cfg, MODELS_DIR / "CONFIG" / f"{name}.json")


def run_stage_ml(df: pd.DataFrame) -> pd.DataFrame:
    """Fit ML on train, produce train+val predictions. Returns long prediction table rows (train+val only)."""
    feats = feature_columns(df)
    rows = []
    for col in TARGETS:
        name = TARGETS[col]
        dtr = df[df["split"] == "train"]
        dva = df[df["split"] == "val"]
        models, scaler, cfg = train_target(dtr, dva, feats, name, col)
        save_models_artifacts(models, scaler, cfg, name)
        for split_label, d in (("train", dtr), ("val", dva)):
            probs = predict_row_arrays(models, d, feats, scaler)
            for mname, p in probs.items():
                rows.append(pd.DataFrame({
                    "date": d["date"].to_numpy(), "cell_id": d["cell_id"].to_numpy(),
                    "target": name, "model": mname, "split": split_label,
                    "probability": p, "observed_label": d[col].to_numpy(),
                }))
        print(f"[stage-ml] fit+:{name}")
    out = pd.concat(rows, ignore_index=True)
    out.to_parquet(PREDICTIONS_DIR / "ml_train_val_predictions.parquet", index=False)
    return out


if __name__ == "__main__":
    df = pd.read_parquet(MATRIX_PATH)
    print("feature columns:", len(feature_columns(df)))
    run_stage_ml(df)
    print("STAGE ML DONE (train+val predictions only)")