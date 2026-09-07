"""Phase H6: validation (2022-2023) metrics for ablation groups vs frozen references."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modeling import evaluate as ev  # noqa: E402
from src.modeling.common import PREDICTIONS_DIR, PROJECT_ROOT, PUBLIC_TARGETS, region_of  # noqa: E402
from src.modeling.metrics import compute_metrics  # noqa: E402
from src.modeling.phase_h import modeling as M  # noqa: E402

# Frozen Phase G winners: target -> (kind, model, config)
FROZEN_G = {
    "onset": {"model": "persistence", "config": None},
    "break": {"model": "persistence", "config": None},
    "revival": {"model": "xgboost", "config": "D_full"},
    "dry_spell": {"model": "persistence", "config": None},
}


def load_frozen_reference_val(df: pd.DataFrame) -> pd.DataFrame:
    """Return val predictions of the frozen Phase G winners for every target."""
    base = pd.read_parquet(PREDICTIONS_DIR / "baseline_predictions.parquet")
    base = base[base["split"] == "val"]
    parts = []
    for tgt in PUBLIC_TARGETS:
        w = FROZEN_G[tgt]
        if w["config"] is None:  # persistence baseline
            d = base[(base["target"] == tgt) & (base["model"] == "persistence")]
        else:
            ml = pd.read_parquet(PREDICTIONS_DIR / "ml_train_val_predictions.parquet")
            d = ml[(ml["target"] == tgt) & (ml["model"] == w["model"]) & (ml["split"] == "val")]
        d = d.copy()
        d["group"] = "REF"
        d["model_display"] = w["model"]
        parts.append(d[["date", "cell_id", "target", "model", "split", "probability",
                        "observed_label", "group"]])
    return pd.concat(parts, ignore_index=True)


def val_metrics_table(preds: pd.DataFrame, ref: pd.DataFrame) -> pd.DataFrame:
    pv = preds[preds["split"] == "val"]
    rv = ref
    recs = ev.aggregate(pv.copy(), groups=("group",))
    rrecs = ev.aggregate(rv.copy(), groups=("group",))
    # align columns
    cols = [c for c in recs[0] if c not in ("reliability", "name")]
    out = pd.DataFrame(recs, columns=cols)
    ro = pd.DataFrame(rrecs, columns=cols)
    out["model"] = out["model"]  # logistic/random_forest/xgboost
    ro["model"] = ro["model"]
    return pd.concat([out, ro], ignore_index=True), cols


def compare_vs_frozen(metrics: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for tgt in PUBLIC_TARGETS:
        ref_rows = metrics[(metrics["target"] == tgt) & (metrics["group"] == "REF")]
        ref_brier = float(ref_rows["brier"].iloc[0])
        for _, r in metrics[(metrics["target"] == tgt) & (metrics["group"] != "REF")].iterrows():
            delta = float(r["brier"]) - ref_brier
            rows.append({
                "target": tgt, "group": r["group"], "model": r["model"],
                "brier": float(r["brier"]), "delta_vs_frozen": delta,
                "pr_auc": r.get("pr_auc"), "roc_auc": r.get("roc_auc"),
                "ece": r.get("ece"), "improves": delta <= -5e-4,
            })
    return pd.DataFrame(rows)


def main() -> None:
    df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "phase_h_matrix.parquet")
    preds = M.load_group_predictions()
    region_map = df.groupby("cell_id")["bbox_guess"].first().map(region_of).to_dict()
    ref = load_frozen_reference_val(df)
    metrics, cols = val_metrics_table(preds, ref)
    metrics.to_parquet(PREDICTIONS_DIR / "phase_h" / "val_metrics_all.parquet", index=False)
    comp = compare_vs_frozen(metrics)
    comp.to_parquet(PREDICTIONS_DIR / "phase_h" / "val_compare_frozen.parquet", index=False)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 20)
    show = metrics[["group", "target", "model", "brier", "pr_auc", "roc_auc", "ece"]].copy()
    show["brier"] = show["brier"].round(5)
    show[["pr_auc", "roc_auc"]] = show[["pr_auc", "roc_auc"]].round(4)
    show["ece"] = show["ece"].round(4)
    for tgt in PUBLIC_TARGETS:
        print(f"\n===== {tgt} =====")
        print(show[show["target"] == tgt].to_string(index=False))
    print("\n===== vs frozen (delta negative = better than frozen ref) =====")
    d = comp[["target", "group", "model", "delta_vs_frozen", "pr_auc", "ece"]].copy()
    d["delta_vs_frozen"] = d["delta_vs_frozen"].round(5)
    print(d[d["delta_vs_frozen"] <= -5e-4].to_string(index=False))


if __name__ == "__main__":
    main()