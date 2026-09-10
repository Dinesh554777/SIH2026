"""Frozen model service.

Loads ONLY frozen Phase H artifacts:
- persistence transitions + cell-dseason climatology (fitted on TRAIN 2015-2021)
- XGBoost revival (Group B, 64 features) + train-fitted SimpleImputer

`predict(cell_id, date)` returns calibrated probabilities for all four targets.
Nothing here fits, tunes, or retrains a model.
"""
from __future__ import annotations

import hashlib
import json

import joblib
import numpy as np
import pandas as pd

from src.modeling.baselines import build_climatology, build_persistence_transitions
from src.modeling.common import TARGETS
from src.serving import config as C
from src.serving.store import ObservationStore


def freeze_digest() -> str:
    data = C.PROCESSED.joinpath("FREEZE_H.json").read_bytes()
    return hashlib.sha256(data).hexdigest()[:16]


def _load_revival():
    from src.serving import config as CFG

    xgb = joblib.load(CFG.REVIVAL_DIR / "xgboost.joblib")
    imputer = joblib.load(CFG.REVIVAL_DIR / "imputer.joblib")
    cfg = json.load(open(CFG.REVIVAL_DIR / "CONFIG.json", encoding="utf-8"))
    features = list(cfg["features"])
    assert len(features) == 64, f"revival feature count != 64: {len(features)}"
    assert "th_accel" in features
    return xgb, imputer, features, cfg


class ModelService:
    def __init__(self, store: ObservationStore, matrix: pd.DataFrame | None = None):
        self.store = store
        self.freeze = json.load(open(C.FREEZE_H, encoding="utf-8"))
        self.freeze_digest = freeze_digest()
        self.clim = build_climatology(matrix if matrix is not None else store.matrix, TARGETS)
        self.trans = build_persistence_transitions(
            matrix if matrix is not None else store.matrix, TARGETS)
        self.xgb, self.imputer, self.revival_features, self.revival_cfg = _load_revival()
        self._clim_lookup = self.clim.set_index(["cell_id", "dseason"])

    # ------------------------------------------------------------------ helpers
    def _clim_prob(self, cell_id: str, dseason: int, target: str) -> float:
        try:
            return float(self._clim_lookup.loc[(cell_id, dseason), f"{target}_clim_p"])
        except KeyError:
            raise ValueError(
                f"no climatology for (cell={cell_id}, dseason={dseason})")

    def _persistence_prob(self, cell_id: str, date: pd.Timestamp, target: str, prev_row) -> float:
        row = self.store.row(cell_id, date)
        ds = int(row["dseason"])
        if ds == 1:
            return self._clim_prob(cell_id, ds, target)

        col = None
        for k, v in {"onset": "onset_active", "break": "break_active",
                     "dry_spell": "dry_spell_active"}.items():
            if k == target:
                col = v
        if prev_row is None or prev_row is None:
            raise LookupError(f"previous-day observation missing for {cell_id} @ {date.date()}")
        prev_label = int(prev_row[col])
        p = self.trans[target]
        return float(p["p11"] if prev_label == 1 else p["p01"])

    # ------------------------------------------------------------------ predict
    def predict(self, cell_id: str, date: pd.Timestamp) -> dict:
        out = {"cell_id": cell_id, "forecast_date": pd.Timestamp(date).date().isoformat()}
        for target in C.PERSISTENCE_TARGETS:
            prev_row = self.store.previous_day(cell_id, date)
            out[target] = {
                "probability": self._persistence_prob(cell_id, date, target, prev_row),
                "model": "persistence",
                "feature_group": "frozen_reference",
            }
        out[C.REVIVAL_TARGET] = self._revival_prob(cell_id, date)
        return out

    def _revival_prob(self, cell_id: str, date: pd.Timestamp) -> dict:
        row = self.store.row(cell_id, date)
        if row is None:
            raise ValueError(f"no row for {cell_id} @ {date}")
        feats = self.revival_features
        X = row[feats].to_numpy(dtype=np.float64).reshape(1, -1)
        X = self.imputer.transform(X)
        p = float(self.xgb.predict_proba(X)[0, 1])
        return {
            "probability": p,
            "model": "xgboost",
            "feature_group": "B_temporal",
            "n_features": len(feats),
        }

    # ------------------------------------------------------------------ evidence
    def sensitivity(self, cell_id: str, date: pd.Timestamp,
                    features: list[str] | None = None) -> list[dict]:
        """One-feature-at-a-time sensitivity on the FROZEN revival model.

        For each listed feature we compare the actual prediction against the
        prediction obtained when that feature is set to its train median (the
        frozen imputer statistic). Descriptive only - NOT a causal statement.
        """
        if features is None:
            features = ["th_accel", "th_sum7", "th_sum10", "th_cv7",
                        "th_wetcount7", "th_wet_streak", "th_dry_streak",
                        "imd_sum7", "imd_sum14", "imd_anom_t"]
        row = self.store.row(cell_id, date)
        X = row[self.revival_features].to_numpy(dtype=np.float64).reshape(1, -1)
        baseline = float(self.xgb.predict_proba(self.imputer.transform(X))[0, 1])
        medians = np.array(self.imputer.statistics_)
        out = []
        for f in features:
            if f not in self.revival_features:
                continue
            j = self.revival_features.index(f)
            X2 = X.copy()
            X2[0, j] = medians[j]
            p2 = float(self.xgb.predict_proba(self.imputer.transform(X2))[0, 1])
            val = float(row[f]) if not pd.isna(row[f]) else float(medians[j])
            mean = float(medians[j])
            out.append({
                "feature": f,
                "value": round(val, 4),
                "train_median": round(mean, 4),
                "delta_probability": round(p2 - baseline, 4),
            })
        out.sort(key=lambda d: -abs(d["delta_probability"]))
        return out

    def observations_used(self, row: pd.Series) -> dict:
        keys = ["imd_rain_t", "imd_sum3", "imd_sum7", "imd_sum14", "imd_days_since_wet",
                "imd_consec_dry", "imd_anom_t", "th_accel", "th_cv7", "th_wet_streak",
                "th_dry_streak", "chirps_rain"]
        out = {}
        for k in keys:
            if k in row.index:
                v = row[k]
                out[k] = None if pd.isna(v) else round(float(v), 4)
        return out

    def provenance(self, target: str | None = None) -> dict:
        tf = self.freeze["targets"]
        base = {
            "freeze_file": str(C.FREEZE_H),
            "freeze_digest": self.freeze_digest,
            "train_period": self.freeze["train_period"],
            "validation_period": self.freeze["validation_period"],
            "test_period": self.freeze["test_period"],
            "note": self.freeze["note"],
            "data_mode": C.DATA_MODE,
            "forecast_horizon_note": C.FORECAST_HORIZON_NOTE,
        }
        if target is not None and target in tf:
            base["target"] = {
                "name": target,
                "selected_model": tf[target]["selected_model"],
                "feature_group": tf[target]["feature_group"],
                "validation_brier": tf[target]["validation_brier"],
                "validation_ece": tf[target]["validation_ece"],
            }
            if target == C.REVIVAL_TARGET:
                base["target"]["model_config"] = {
                    k: tf[target]["hyperparameters"][k]
                    for k in ("n_estimators", "max_depth", "learning_rate", "seed")
                }
                base["target"]["trained_at"] = self.revival_cfg["trained_at"]
                base["target"]["versions"] = self.revival_cfg["versions"]
        return base


_DEFAULT: ModelService | None = None


def default_service(store: ObservationStore) -> "ModelService":
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = ModelService(store, matrix=store.matrix)
    return _DEFAULT