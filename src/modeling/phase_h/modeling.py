"""Phase H5/H6 modeling harness.

- Groups: A = frozen Phase-G full (51 predictors); B/C/D/E = A + temporal/seasonal/
  event-state/spatial representations. Group F is only constructed later if validation
  justifies it.
- Imputation: SimpleImputer(strategy="median") fitted on TRAIN (2015-2021) ONLY, applied
  to the structural boundary NaNs (th_rstd7, th_rstd14, sp_mean_lag1) on train/val/test
  with the frozen statistic. Persistence baseline is untouched (existing artifact).
- Models: logistic / random_forest / xgboost, hyperparameters identical to Phases E-G.
- 2024 (test) is NOT touched here; only train+val predictions with observed labels.
"""
from __future__ import annotations

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src.modeling.common import (PREDICTIONS_DIR, PROJECT_ROOT, RANDOM_SEED, TARGETS,
                                 feature_columns, pkg_versions, utcnow, write_json)

PH_MODELS_DIR = PROJECT_ROOT / "models" / "phase_h"
PH_PRED_DIR = PREDICTIONS_DIR / "phase_h"

ML_MODELS = ["logistic", "random_forest", "xgboost"]
NEW_PREFIXES = ("th_", "sh_", "es_", "sp_")
# Features expected to carry structural season-boundary NaNs (imputed, train-only statistic)
IMPUTED_FEATURES = ("th_rstd7", "th_rstd14", "sp_mean_lag1")

GROUPS = ("A", "B", "C", "D", "E")


def group_features(matrix: pd.DataFrame, group: str) -> list[str]:
    """Deterministic feature list for a Phase H group (A = frozen 51)."""
    A = feature_columns(matrix)  # 51 frozen predictors
    if group == "A":
        return list(A)
    prefix = {"B": "th_", "C": "sh_", "D": "es_", "E": "sp_"}[group]
    add = [c for c in matrix.columns if c.startswith(prefix) and c not in A]
    return list(A) + add


def all_groups_matrix(matrix: pd.DataFrame) -> pd.DataFrame:
    """Return matrix with imputed columns baked in (train-only median per feature)."""
    out = matrix.copy()
    imp = np.nanmedian(matrix.loc[matrix["split"] == "train", list(IMPUTED_FEATURES)],
                       axis=0)
    for f, v in zip(IMPUTED_FEATURES, imp):
        if np.isnan(v):
            v = 0.0
        out[f] = matrix[f].fillna(v)
    return out


class TrainOnlyImputer:
    """Skeleton for explicit documentation; actual imputation is inline in fit/predict."""


def train_target(df_train, df_val, feats, name: str, col: str):
    """Fit all three ML models for one target+group on TRAIN only.

    Returns (models, scaler, imputer, cfg). The imputer is a SimpleImputer(median)
    fitted on TRAIN only so the same statistic is frozen for val and test.
    """
    imp = SimpleImputer(strategy="median")
    Xtr = imp.fit_transform(df_train[feats].to_numpy(dtype=np.float64))
    Xva = imp.transform(df_val[feats].to_numpy(dtype=np.float64))
    ytr = df_train[col].to_numpy(dtype=np.float64)
    yva = df_val[col].to_numpy(dtype=np.float64)
    pos = int(ytr.sum()); neg = int(len(ytr) - pos)

    models = {}

    scaler = StandardScaler().fit(Xtr)
    lr = LogisticRegression(C=1.0, class_weight="balanced", solver="lbfgs",
                            max_iter=2000, random_state=RANDOM_SEED)
    lr.fit(scaler.transform(Xtr), ytr)
    models["logistic"] = lr

    rf = RandomForestClassifier(n_estimators=250, max_depth=14, min_samples_leaf=20,
                                class_weight="balanced", n_jobs=-1, random_state=RANDOM_SEED)
    rf.fit(Xtr, ytr)
    models["random_forest"] = rf

    xg = xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1,
                           subsample=0.9, colsample_bytree=0.9,
                           scale_pos_weight=neg / max(pos, 1),
                           tree_method="hist", n_jobs=-1, random_state=RANDOM_SEED,
                           eval_metric="logloss")
    xg.fit(Xtr, ytr)
    models["xgboost"] = xg

    cfg = {
        "target": name, "features": feats,
        "n_train": int(len(Xtr)), "n_val": int(len(Xva)),
        "n_pos_train": pos, "n_neg_train": neg,
        "imputation": {"method": "SimpleImputer(strategy='median')", "fit_split": "train",
                       "imputed_features": list(IMPUTED_FEATURES),
                       "statistics": imp.statistics_.tolist()},
        "logistic": {"C": 1.0, "class_weight": "balanced", "solver": "lbfgs",
                     "scaling": "StandardScaler fit on train"},
        "random_forest": {"n_estimators": 250, "max_depth": 14, "min_samples_leaf": 20,
                          "class_weight": "balanced"},
        "xgboost": {"n_estimators": 300, "max_depth": 6, "learning_rate": 0.1,
                    "subsample": 0.9, "colsample_bytree": 0.9,
                    "scale_pos_weight": round(neg / max(pos, 1), 3), "tree_method": "hist"},
        "seed": RANDOM_SEED,
        "fit_split": "train (2015-2021)",
        "trained_at": utcnow(),
        "versions": pkg_versions(),
    }
    return models, scaler, imp, cfg


def predict_row_arrays(models: dict, df, feats, scaler, imputer) -> dict[str, np.ndarray]:
    X = imputer.transform(df[feats].to_numpy(dtype=np.float64))
    out = {}
    for name, m in models.items():
        if name == "logistic":
            out[name] = m.predict_proba(scaler.transform(X))[:, 1]
        else:
            out[name] = m.predict_proba(X)[:, 1]
    return out


def _save_artifacts(models, scaler, imp, cfg, name, group) -> None:
    d = PH_MODELS_DIR / group / name
    d.mkdir(parents=True, exist_ok=True)
    for mname, model in models.items():
        joblib.dump(model, d / f"{mname}.joblib")
    joblib.dump(scaler, d / "scaler.joblib")
    joblib.dump(imp, d / "imputer.joblib")
    write_json(cfg, d / "CONFIG.json")


def run_group(df: pd.DataFrame, group: str) -> None:
    """Fit all targets for one group; write train+val prediction rows (long format)."""
    feats = group_features(df, group)
    imp_df = all_groups_matrix(df)
    dtr = imp_df[imp_df["split"] == "train"]
    dva = imp_df[imp_df["split"] == "val"]
    rows = []
    for col, name in TARGETS.items():
        models, scaler, imp, cfg = train_target(dtr, dva, feats, name, col)
        _save_artifacts(models, scaler, imp, cfg, name, group)
        for split_label, d in (("train", dtr), ("val", dva)):
            probs = predict_row_arrays(models, d, feats, scaler, imp)
            for mname, p in probs.items():
                rows.append(pd.DataFrame({
                    "date": d["date"].to_numpy(), "cell_id": d["cell_id"].to_numpy(),
                    "target": name, "model": mname, "split": split_label,
                    "probability": p, "observed_label": d[col].to_numpy(),
                    "group": group,
                }))
        print(f"[phase_h] group {group} fit {name} ({len(feats)} feats)")
    out = pd.concat(rows, ignore_index=True)
    out.to_parquet(PH_PRED_DIR / f"group_{group}_train_val.parquet", index=False)
    return out


def load_group_predictions(groups: tuple[str, ...] = GROUPS) -> pd.DataFrame:
    parts = []
    for g in groups:
        f = PH_PRED_DIR / f"group_{g}_train_val.parquet"
        if f.exists():
            parts.append(pd.read_parquet(f))
        else:
            print(f"[warn] missing: {f.name}")
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def run_ablation(df: pd.DataFrame, groups: tuple[str, ...] = GROUPS) -> pd.DataFrame:
    PH_PRED_DIR.mkdir(parents=True, exist_ok=True)
    for g in groups:
        out_path = PH_PRED_DIR / f"group_{g}_train_val.parquet"
        if out_path.exists():
            print(f"[phase_h] skip group {g} (predictions exist)")
            continue
        run_group(df, g)
    return load_group_predictions(groups)


if __name__ == "__main__":
    import pandas as pd
    ph = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "phase_h_matrix.parquet")
    print("feature columns (Group A):", len(feature_columns(ph)))
    for g in GROUPS:
        print(f"group {g}: {len(group_features(ph, g))} features")
    print("Running H5 ablation (train+val only; 2024 untouched)")
    run_ablation(ph)
    print("H5 ablation done")