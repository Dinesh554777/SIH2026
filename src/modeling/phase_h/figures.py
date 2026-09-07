"""Phase H figures: feature ablation (validation Brier per group) + calibration."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modeling.common import FIGURES_DIR, PUBLIC_TARGETS  # noqa: E402
from src.modeling.metrics import reliability  # noqa: E402

ML = ["logistic", "random_forest", "xgboost"]
GROUPS = ["A", "B", "C", "D", "E"]
G_LABEL = {"A": "A (frozen 51)", "B": "B (+temporal)", "C": "C (+seasonal)",
           "D": "D (+event-state)", "E": "E (+spatial)"}


def fig_ablation() -> None:
    m = pd.read_parquet("data/processed/predictions/phase_h/val_metrics_all.parquet")
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    for ax, tgt in zip(axes.flat, PUBLIC_TARGETS):
        d = m[m["target"] == tgt]
        x = np.arange(len(GROUPS)); w = 0.26
        for k, mod in enumerate(ML):
            vals = [float(d.loc[(d["group"] == g) & (d["model"] == mod), "brier"].iloc[0])
                    for g in GROUPS]
            ax.bar(x + (k - 1) * w, vals, w, label=mod)
        # frozen persistence line
        ref = d[d["group"] == "REF"]
        if len(ref):
            ax.axhline(float(ref["brier"].iloc[0]), ls="--", c="black", lw=1.5)
            ax.text(0.02, float(ref["brier"].iloc[0]), f"frozen ref {float(ref['brier'].iloc[0]):.4f}",
                    va="bottom", fontsize=8, transform=ax.get_yaxis_transform())
        ax.set_xticks(x); ax.set_xticklabels([G_LABEL[g] for g in GROUPS], rotation=25, fontsize=8)
        ax.set_title(f"{tgt} — validation Brier by group (lower better)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
    fig.savefig(FIGURES_DIR / "phase_h_feature_ablation.png", dpi=130)
    plt.close(fig)
    print("wrote phase_h_feature_ablation.png")


def fig_calibration() -> None:
    # revival candidate B/xgb vs frozen, reliability diagrams
    preds = pd.read_parquet("data/processed/predictions/phase_h/group_B_train_val.parquet")
    # revive predictions for candidate B/xgb (val)
    d = preds[(preds["target"] == "revival") & (preds["group"] == "B") &
              (preds["model"] == "xgboost") & (preds["split"] == "val")]
    ml = pd.read_parquet("data/processed/predictions/ml_train_val_predictions.parquet")
    frozen = ml[(ml["target"] == "revival") & (ml["model"] == "xgboost") & (ml["split"] == "val")]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), constrained_layout=True)
    for ax, (label, yy, pp) in zip(axes, (
            ("Phase G frozen XGB (D_full)", frozen["observed_label"].to_numpy(), frozen["probability"].to_numpy()),
            ("Phase H XGB + temporal (B)", d["observed_label"].to_numpy(), d["probability"].to_numpy()))):
        rel = reliability(yy, pp)
        ax.plot([0, 1], [0, 1], "--", color="grey")
        ax.plot([r["bin_mean_pred"] for r in rel], [r["bin_freq"] for r in rel],
                marker="o", ms=4)
        ax.set_title(f"revival · {label}\n(n={len(yy)}, pos={int(yy.sum())})", fontsize=9)
        ax.set_xlabel("predicted"); ax.set_ylabel("observed")
        ax.grid(alpha=0.3); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    fig.savefig(FIGURES_DIR / "phase_h_calibration.png", dpi=130)
    plt.close(fig)
    print("wrote phase_h_calibration.png")


if __name__ == "__main__":
    fig_ablation()
    fig_calibration()