"""Phase H9: single 2024 test evaluation of the frozen Phase H architecture.

Runs exactly once, AFTER FREEZE_H.json is written. Compares Phase G frozen
vs Phase H frozen for every target. No tuning or re-selection occurs after seeing
these results.

Phase G frozen:   onset/break/dry_spell = persistence; revival = XGBoost D_full (51 feats)
Phase H frozen:   onset/break/dry_spell = persistence (unchanged); revival = XGBoost B (64 feats, temporal)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modeling.common import (FREEZE_PATH, PREDICTIONS_DIR, PROJECT_ROOT,  # noqa: E402
                                 PUBLIC_TARGETS)
from src.modeling.metrics import compute_metrics  # noqa: E402
from src.modeling.phase_h import modeling as M  # noqa: E402

PHASE_G_FROZEN = {  # target -> (model, config) decided in FREEZE_G.json
    "onset": ("persistence", None),
    "break": ("persistence", None),
    "revival": ("xgboost", "D_full"),
    "dry_spell": ("persistence", None),
}
PHASE_H_FROZEN = {  # target -> (group, model) per FREEZE_H.json
    "onset": ("REF", "persistence"),
    "break": ("REF", "persistence"),
    "revival": ("B", "xgboost"),
    "dry_spell": ("REF", "persistence"),
}


def phase_g_test_preds(target: str) -> pd.DataFrame:
    model, config = PHASE_G_FROZEN[target]
    base = pd.read_parquet(PREDICTIONS_DIR / "baseline_predictions.parquet")
    base = base[(base["split"] == "test") & (base["target"] == target) &
                (base["model"] == "persistence")]
    if config is None:
        return base
    # revival learned (Phase G): use the D_full test predictions already produced for 2024
    tg = pd.read_parquet(PREDICTIONS_DIR / "ablation_test_predictions.parquet")
    d = tg[(tg["target"] == target) & (tg["model"] == model) & (tg["config"] == config)]
    return d


FREEZE_H = PROJECT_ROOT / "data" / "processed" / "FREEZE_H.json"


def freeze_exists() -> bool:
    return Path(FREEZE_H).exists()


def evaluate_once() -> dict:
    freeze_ok = freeze_exists()
    assert freeze_ok, "FREEZE_H.json must exist before 2024 evaluation"
    ph = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "phase_h_matrix.parquet")
    imp_df = M.all_groups_matrix(ph)
    dte = imp_df[imp_df["split"] == "test"]
    rows = []
    for target in PUBLIC_TARGETS:
        hg = PHASE_H_FROZEN[target]
        if hg[0] == "REF":  # persistence (Phase H keeps Phase G reference)
            gog = phase_g_test_preds(target)
            rows.append(pd.DataFrame({
                "target": target, "phase": "G_FROZEN", "model": "persistence",
                "probability": gog["probability"].to_numpy(),
                "observed_label": gog["observed_label"].to_numpy(),
            }))
            rows.append(pd.DataFrame({
                "target": target, "phase": "H_FROZEN", "model": "persistence",
                "probability": gog["probability"].to_numpy(),
                "observed_label": gog["observed_label"].to_numpy(),
            }))
        else:  # revival candidate XGBoost B
            group, model = hg
            feats = M.group_features(ph, group)
            cfg = __import__("json").load(
                open(PROJECT_ROOT / "models" / "phase_h" / group / target / "CONFIG.json"))
            xg = __import__("joblib").load(
                PROJECT_ROOT / "models" / "phase_h" / group / target / "xgboost.joblib")
            imp = __import__("joblib").load(
                PROJECT_ROOT / "models" / "phase_h" / group / target / "imputer.joblib")
            X = imp.transform(dte[feats].to_numpy(dtype=np.float64))
            p_h = xg.predict_proba(X)[:, 1]
            rows.append(pd.DataFrame({
                "target": target, "phase": "H_FROZEN", "model": model,
                "probability": p_h, "observed_label": dte["revival_day"].to_numpy(),
            }))
            # Phase G frozen revival = XGBoost D_full
            gog = phase_g_test_preds(target)
            # align by (cell_id, date) is safe: same matrix order
            rows.append(pd.DataFrame({
                "target": target, "phase": "G_FROZEN", "model": "xgboost_Dfull",
                "probability": gog["probability"].to_numpy(),
                "observed_label": gog["observed_label"].to_numpy(),
            }))
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    test = evaluate_once()
    test.to_parquet(PREDICTIONS_DIR / "phase_h" / "test_2024_frozen.parquet", index=False)
    print("FREEZE_H exists:", freeze_exists())
    print("TEST — 2024 — frozen Phase G vs Phase H (single evaluation pass)")
    for target in PUBLIC_TARGETS:
        print(f"\n===== {target} (TEST 2024) =====")
        for phase in ("G_FROZEN", "H_FROZEN"):
            d = test[(test["target"] == target) & (test["phase"] == phase)]
            m = compute_metrics(d["observed_label"].to_numpy(), d["probability"].to_numpy())
            print(f"  {phase:8s} {m['model'] if 'model' in m else 'xgb'}: brier={m['brier']:.5f} "
                  f"pr_auc={m['pr_auc']} roc={m['roc_auc']} prec={m['precision']:.3f} "
                  f"rec={m['recall']:.3f} f1={m['f1']:.3f} ece={m['ece']:.4f} n_pos={m['n_pos']}")


if __name__ == "__main__":
    main()