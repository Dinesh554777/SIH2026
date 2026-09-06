"""Phase E + F run.

Stage 1: baselines (climatology, persistence) -> all splits (fixed references).
Stage 2: ML (logistic/RF/XGB) fitted on TRAIN only; train+val predictions.
Stage 3: validation analysis (metrics, yearly 2022-23, regional, figures).
Stage 4: FROZEN model selection using VALIDATION ONLY -> MODEL_SELECTION_DECISION.md + FREEZE.json.
Stage 5: (only after FREEZE exists) evaluate 2024 exactly once + write reports.

Nothing in this module reads or writes 2024 test labels before Stage 5.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modeling import evaluate as ev  # noqa: E402
from src.modeling.baselines import (  # noqa: E402
    baseline_predictions, build_climatology, build_persistence_transitions,
    write_baseline_metadata)
from src.modeling.common import (  # noqa: E402
    FIGURES_DIR, FREEZE_PATH, MATRIX_PATH, MODELS_DIR, PREDICTIONS_DIR,
    PROJECT_ROOT, PUBLIC_TARGETS, RANDOM_SEED, TARGETS, feature_columns,
    mkdirs, pkg_versions, region_of, utcnow, write_json)
from src.modeling.integrity_check import run_integrity_check  # noqa: E402
from src.modeling.train_ml import run_stage_ml, predict_row_arrays  # noqa: E402
import joblib  # noqa: E402


def load_stage2(feats: list[str]):
    ml_vals = pd.read_parquet(PREDICTIONS_DIR / "ml_train_val_predictions.parquet")
    df = pd.read_parquet(MATRIX_PATH)
    test_models = {}
    for col in TARGETS:
        name = TARGETS[col]
        d = dict()
        for mname in ("logistic", "random_forest", "xgboost"):
            d[mname] = (joblib.load(MODELS_DIR / mname / name / "model.joblib"),
                        joblib.load(MODELS_DIR / mname / name / "scaler.joblib"))
        test_models[name] = d
    return ml_vals, df, test_models


def test_predictions(df, models, feats) -> pd.DataFrame:
    dte = df[df["split"] == "test"]
    rows = []
    for col, name in TARGETS.items():
        X = dte[feats].to_numpy(dtype=float)
        for mname, (model, scaler) in models[name].items():
            p = model.predict_proba(scaler.transform(X) if mname == "logistic" else X)[:, 1]
            rows.append(pd.DataFrame({
                "date": dte["date"].to_numpy(), "cell_id": dte["cell_id"].to_numpy(),
                "target": name, "model": mname, "split": "test",
                "probability": p, "observed_label": dte[col].to_numpy(),
            }))
        print(f"[test] predictions: {name}")
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    mkdirs()
    print("=" * 60)
    print("STAGE 0: integrity check")
    ic = run_integrity_check()
    write_json(ic, PROJECT_ROOT / "reports" / "PRETRAINING_INTEGRITY_CHECK.json")

    df = pd.read_parquet(MATRIX_PATH)
    feats = feature_columns(df)
    region_map = df.groupby("cell_id")["bbox_guess"].first().map(region_of).to_dict()

    print("STAGE 1: baselines")
    clim = build_climatology(df, TARGETS)
    trans = build_persistence_transitions(df, TARGETS)
    pred_base = baseline_predictions(df, clim, trans, TARGETS)
    pred_base.to_parquet(PREDICTIONS_DIR / "baseline_predictions.parquet", index=False)
    write_json(write_baseline_metadata(clim, trans),
               PROJECT_ROOT / "reports" / "BASELINE_CONSTRUCTION.json")

    print("STAGE 2: ML train on TRAIN only; train+val predictions")
    pred_ml = run_stage_ml(df)

    print("STAGE 3: validation analysis (2022-2023)")
    val = pd.concat([pred_base, pred_ml], ignore_index=True)
    val = val[val["split"] == "val"]
    val = ev._augment(val, region_map)
    val_metrics = ev.aggregate(val, groups=("split",))
    write_json(val_metrics, PREDICTIONS_DIR / "val_metrics.json")
    val_df = ev.dframe(val_metrics)
    val_df[val_df["split"] == "val"].to_csv(PREDICTIONS_DIR / "val_metrics.csv", index=False)
    val_yearly = ev.aggregate(val, groups=("year",))
    write_json(val_yearly, PREDICTIONS_DIR / "val_yearly_metrics.json")
    val_region = ev.aggregate(val, groups=("split", "region"))
    write_json(val_region, PREDICTIONS_DIR / "val_region_metrics.json")
    ev.plot_brier_bar(val_df, "brier_validation.png")
    ev.plot_calibration(val, split="val")
    ev.plot_roc_pr(val, split="val")
    ev.plot_obs_vs_pred(val, split="val")
    print(_fmt_table(val_df))

    print("STAGE 4: FROZEN model selection (validation only)")
    decision = choose_winners(val_df)
    freeze = {
        "decision": decision,
        "frozen_at": utcnow(),
        "seed": RANDOM_SEED,
        "rule": "winner = learned model that materiallly improves validation Brier "
                "over BOTH climatology and persistence (>=0.001) and has a defined ROC-AUC; "
                "tie-break lowest validation ECE then lowest Brier; otherwise the better "
                "baseline (climatology vs persistence) is declared winner.",
        "note": "2024 TEST LABELS WERE NOT USED at any point up to and including this freeze.",
        "packages": pkg_versions(),
    }
    write_json(freeze, FREEZE_PATH)
    print(json.dumps(decision, indent=2))

    if not FREEZE_PATH.exists():
        sys.exit("FREEZE NOT CREATED — aborting, test left untouched.")

    print("STAGE 5: FINAL TEST EVALUATION (2024) — once, after freeze")
    ml_vals, df, models = load_stage2(feats)
    pred_test = test_predictions(df, models, feats)
    pred_test.to_parquet(PREDICTIONS_DIR / "ml_test_predictions.parquet", index=False)
    full = pd.concat([pd.read_parquet(PREDICTIONS_DIR / "baseline_predictions.parquet"),
                      ml_vals, pred_test], ignore_index=True)
    full.to_parquet(PREDICTIONS_DIR / "all_predictions.parquet", index=False)

    test = pd.concat([
        pd.read_parquet(PREDICTIONS_DIR / "baseline_predictions.parquet").query("split == 'test'"),
        pred_test,
    ], ignore_index=True)
    test = ev._augment(test, region_map)
    test_metrics = ev.aggregate(test, groups=("split",))
    write_json(test_metrics, PREDICTIONS_DIR / "test_metrics.json")
    ev.dframe(test_metrics).to_csv(PREDICTIONS_DIR / "test_metrics.csv", index=False)
    test_yearly = ev.aggregate(test, groups=("year",))
    write_json(test_yearly, PREDICTIONS_DIR / "test_yearly_metrics.json")
    test_region = ev.aggregate(test, groups=("split", "region"))
    write_json(test_region, PREDICTIONS_DIR / "test_region_metrics.json")

    ev.plot_brier_bar(pd.concat([ev.dframe(val_metrics), ev.dframe(test_metrics)]),
                      "brier_val_test.png")
    ev.plot_calibration(ev._augment(full, region_map),
                        split="test", fname="calibration_test.png")
    ev.plot_roc_pr(ev._augment(pred_test, region_map), split="test")
    ev.plot_obs_vs_pred(ev._augment(pred_test, region_map), split="test")
    ev.plot_yearly(ev._augment(full, region_map))

    print("Writing reports...")
    from src.modeling import reporting
    reporting.write_all_reports(val_df, test_metrics, val_yearly, test_yearly,
                                val_region, test_region, decision, full)
    print("==================================================================")
    print("PHASES E-F COMPLETE")
    print("===================")
    print("Targets: onset break revival dry_spell")
    print("Models: climatology persistence logistic random_forest xgboost")
    print("Reports: BASELINE_MODEL_COMPARISON.md PROBABILISTIC_EVALUATION_REPORT.md ",
          "YEARLY_GENERALIZATION_REPORT.md REGIONAL_PERFORMANCE_REPORT.md ",
          "MODEL_SELECTION_DECISION.md PHASES_E_F_COMPLETION_REPORT.md")
    print("Test set: 2024 untouched until final evaluation")
    print("Next decision: WAITING FOR HUMAN APPROVAL")
    print("==================================================================")


def choose_winners(val_df: pd.DataFrame) -> dict:
    per_target = {}
    for tgt in PUBLIC_TARGETS:
        d = val_df[val_df["target"] == tgt]
        b_clim = float(d.loc[d["model"] == "climatology", "brier"].iloc[0])
        b_pers = float(d.loc[d["model"] == "persistence", "brier"].iloc[0])
        learned = []
        for m in ("logistic", "random_forest", "xgboost"):
            r = d[d["model"] == m]
            if r.empty: continue
            b = float(r["brier"].iloc[0])
            auc = r["roc_auc"].iloc[0]
            ece = float(r["ece"].iloc[0])
            if (b <= b_clim - 1e-3) and (b <= b_pers - 1e-3) and auc is not None:
                learned.append((m, ece, b))
        if learned:
            learned.sort(key=lambda t: (round(t[1], 6), t[2]))
            winner = learned[0][0]; kind = "learned"
        else:
            winner = "climatology" if b_clim <= b_pers else "persistence"
            kind = "baseline"
        per_target[tgt] = {
            "winner": winner, "kind": kind,
            "val_brier_climatology": round(b_clim, 5),
            "val_brier_persistence": round(b_pers, 5),
        }
    return {"winner": per_target}


def _fmt_table(records_df: pd.DataFrame) -> str:
    cols = [c for c in ("split", "target", "model", "brier", "log_loss", "roc_auc", "pr_auc",
                        "precision", "recall", "f1", "ece", "positive_rate") if c in records_df]
    return records_df[cols].to_string(index=False)


if __name__ == "__main__":
    main()