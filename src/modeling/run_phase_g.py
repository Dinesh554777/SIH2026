"""Phase G — Feature ablation run.

G1: configs + lightweight integrity.
G2: fit logistic/RF/XGB for configs A/B/C on TRAIN only (resumable); D reuses E/F.
G3: validation metrics per (config, target, model) + baseline reference + feature importances.
G4: FROZEN per-target (config, model) selected on VALIDATION ONLY -> FREEZE_G.json.
G5: evaluate 2024 exactly once (post-freeze) for all ablation configs; write reports.

2024 labels are not opened before Stage G5.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modeling import evaluate as ev  # noqa: E402
from src.modeling.ablation import (  # noqa: E402
    ABLATION_DIR, make_configs, load_ablation_predictions, run_ablation)
from src.modeling.common import (  # noqa: E402
    FIGURES_DIR, MATRIX_PATH, MODELS_DIR, PREDICTIONS_DIR, PROJECT_ROOT,
    PUBLIC_TARGETS, RANDOM_SEED, TARGETS, feature_columns, pkg_versions,
    region_of, utcnow, write_json)
from src.modeling.metrics import compute_metrics  # noqa: E402
from src.modeling.train_ml import predict_row_arrays  # noqa: E402

FREEZE_G = PROJECT_ROOT / "data" / "processed" / "FREEZE_G.json"
ML_MODELS = ["logistic", "random_forest", "xgboost"]


def _val_metrics(preds_val: pd.DataFrame, region_map) -> list[dict]:
    return ev.aggregate(preds_val.copy().assign(config=preds_val["config"], split="val"),
                        groups=("config",))


def baseline_ref(df) -> dict:
    base = pd.read_parquet(PREDICTIONS_DIR / "baseline_predictions.parquet")
    base = base[base["split"] == "val"]
    out = {}
    for tgt in PUBLIC_TARGETS:
        for mod in ("climatology", "persistence"):
            d = base[(base["target"] == tgt) & (base["model"] == mod)]
            m = compute_metrics(d["observed_label"].to_numpy(), d["probability"].to_numpy())
            out[tgt + "/" + mod] = m
    return out


def plot_ablation_brier(records) -> None:
    df = pd.DataFrame(records)
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    cfgs = ["A_imd", "B_imd_chirps", "C_imd_chirps_oni", "D_full"]
    for ax, tgt in zip(axes.flat, PUBLIC_TARGETS):
        d = df[df["target"] == tgt]
        x = np.arange(len(cfgs)); w = 0.26
        for k, m in enumerate(ML_MODELS):
            vals = []
            for c in cfgs:
                r = d[(d["config"] == c) & (d["model"] == m)]
                vals.append(float(r["brier"].iloc[0]) if len(r) else np.nan)
            ax.bar(x + (k - 1) * w, vals, w, label=m)
        ax.set_xticks(x); ax.set_xticklabels([c[:7] for c in cfgs], rotation=30)
        ax.set_title(f"{tgt} — validation Brier by config")
        ax.legend(fontsize=8)
    fig.savefig(FIGURES_DIR / "ablation_brier_val.png", dpi=130)
    plt.close(fig)


def feature_importances(df) -> dict:
    feats = feature_columns(df)
    out = {}
    for col, name in TARGETS.items():
        # XGBoost gain importances (full-feature E/F model)
        xg = joblib.load(MODELS_DIR / "xgboost" / name / "model.joblib")
        gain = xg.get_booster().get_score(importance_type="gain")
        gain_map = {}
        for k, v in gain.items():
            try:
                idx = int(k[1:])
            except ValueError:
                continue
            if idx < len(feats):
                gain_map[feats[idx]] = v
        top = sorted(gain_map.items(), key=lambda kv: -kv[1])[:15]
        out[name] = {"xgboost_gain_top15": top, "feature_list": feats}
    return out


def freeze_rule(val_records: list[dict], baseline: dict) -> dict:
    """Pick (config, model) per target using validation only."""
    per_target = {}
    for tgt in PUBLIC_TARGETS:
        rows = [r for r in val_records if r["target"] == tgt]
        b_clim = baseline[tgt + "/climatology"]["brier"]
        b_pers = baseline[tgt + "/persistence"]["brier"]
        learned = []
        for r in rows:
            if r["model"] not in ML_MODELS:
                continue
            if r["brier"] <= b_clim - 1e-3 and r["brier"] <= b_pers - 1e-3 and r["roc_auc"] is not None:
                learned.append((r["config"], r["model"], r["brier"], r["ece"]))
        if learned:
            learned.sort(key=lambda t: (round(t[3], 6), t[2]))
            cfg, model, brier, ece = learned[0]
            per_target[tgt] = {"config": cfg, "model": model, "kind": "learned",
                               "val_brier": brier, "val_ece": ece,
                               "baseline_brier_min": min(b_clim, b_pers)}
        else:
            base = "climatology" if b_clim <= b_pers else "persistence"
            per_target[tgt] = {"config": None, "model": base, "kind": "baseline",
                               "val_brier": min(b_clim, b_pers), "val_ece": baseline[tgt + "/" + base]["ece"],
                               "baseline_brier_min": min(b_clim, b_pers)}
    return {"winner": per_target}


def test_predictions_for(df, configs) -> pd.DataFrame:
    dte = df[df["split"] == "test"]
    rows = []
    for cfg_name, cfg_feats in configs.items():
        if cfg_name == "D_full":
            d = pd.read_parquet(PREDICTIONS_DIR / "ml_test_predictions.parquet")
            d["config"] = "D_full"
            rows.append(d)
            continue
        for col, name in TARGETS.items():
            models = {}
            scaler = None
            for mname in ML_MODELS:
                base = MODELS_DIR / "ablation" / cfg_name / name / mname
                models[mname] = joblib.load(base / "model.joblib")
                if mname == "logistic":
                    scaler = joblib.load(base / "scaler.joblib")
            probs = predict_row_arrays(models, dte, cfg_feats, scaler)
            for mname, p in probs.items():
                rows.append(pd.DataFrame({
                    "date": dte["date"].to_numpy(), "cell_id": dte["cell_id"].to_numpy(),
                    "target": name, "model": mname, "split": "test",
                    "probability": p, "observed_label": dte[col].to_numpy(),
                    "config": cfg_name,
                }))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def main() -> None:
    df = pd.read_parquet(MATRIX_PATH)
    configs = make_configs(df)
    for k, v in configs.items():
        print(f"[config] {k}: {len(v)} features")
    region_map = df.groupby("cell_id")["bbox_guess"].first().map(region_of).to_dict()

    print("G2: fitting ablation configs A/B/C (D reused from E/F)")
    run_ablation(df, configs)
    preds = load_ablation_predictions(configs)

    print("G3: validation metrics + feature importances")
    preds_val = preds[preds["split"] == "val"]
    records = _val_metrics(preds_val, region_map)
    write_json(records, PREDICTIONS_DIR / "ablation_val_metrics.json")
    baseline = baseline_ref(df)
    write_json(baseline, PREDICTIONS_DIR / "ablation_baseline_metrics.json")
    imp = feature_importances(df)
    write_json(imp, PROJECT_ROOT / "reports" / "FEATURE_IMPORTANCES.json")
    dfm = pd.DataFrame(records)
    print(dfm[["config", "target", "model", "brier", "roc_auc", "ece"]].to_string(index=False))
    plot_ablation_brier(records)

    print("G4: freeze per-target (config, model) on validation only")
    decision = freeze_rule(records, baseline)
    freeze = {
        "decision": decision,
        "frozen_at": utcnow(),
        "seed": RANDOM_SEED,
        "note": "2024 TEST LABELS NOT USED up to and including this freeze.",
        "packages": pkg_versions(),
    }
    write_json(freeze, FREEZE_G)
    print(json.dumps(decision, indent=2))

    print("G5: final test evaluation (2024) — post-freeze, once")
    test_preds = test_predictions_for(df, configs)
    test_preds.to_parquet(PREDICTIONS_DIR / "ablation_test_predictions.parquet", index=False)
    test_tap = test_preds
    test_records = ev.aggregate(test_tap.copy().assign(config=test_tap["config"]),
                                groups=("config",))
    write_json(test_records, PREDICTIONS_DIR / "ablation_test_metrics.json")
    pd.DataFrame(test_records).to_csv(PREDICTIONS_DIR / "ablation_test_metrics.csv", index=False)

    # frozen-winner test row for headline
    frozen_test = {}
    for tgt, v in decision["winner"].items():
        if v["kind"] == "learned":
            r = next((x for x in test_records if x["target"] == tgt and x["config"] == v["config"]
                      and x["model"] == v["model"]), None)
            frozen_test[tgt] = r
    write_json(frozen_test, PREDICTIONS_DIR / "ablation_frozen_test.json")

    import src.modeling.report_g as report_g
    report_g.write_all(df, configs, records, test_records, baseline, decision, imp)
    print("==================================================================")
    print("PHASE G COMPLETE")
    print("Configs: A_imd B_imd_chirps C_imd_chirps_oni D_full (E/F reference)")
    print("Reports: FEATURE_ABLATION_REPORT.md FEATURE_IMPORTANCES.json PHASE_G_COMPLETION_REPORT.md")
    print("Next decision: WAITING FOR HUMAN APPROVAL (gate before Phase H)")
    print("==================================================================")


if __name__ == "__main__":
    main()