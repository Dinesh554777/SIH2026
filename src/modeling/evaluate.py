"""Phase F evaluation: per-split, yearly, regional metrics + figures (matplotlib Agg)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.modeling.common import FIGURES_DIR, PUBLIC_TARGETS, region_of  # noqa: E402
from src.modeling.metrics import compute_metrics  # noqa: E402


def _augment(preds: pd.DataFrame, region_map: dict[str, str]) -> pd.DataFrame:
    out = preds.copy()
    out["year"] = pd.to_datetime(out["date"]).dt.year.astype(int)
    out["region"] = out["cell_id"].map(region_map)
    return out


def aggregate(preds: pd.DataFrame, groups) -> dict:
    """Compute metric dicts grouped by (target, model, <groups...>).

    Returns {tuple_key: {metric...}} plus a flat record list for tables.
    """
    records = []
    keys = ("target", "model") + tuple(groups)
    for key_vals, grp in preds.groupby(list(keys)):
        m = compute_metrics(grp["observed_label"].to_numpy(),
                            grp["probability"].to_numpy(),
                            name=", ".join(map(str, key_vals)))
        rec = {k: v for k, v in zip(keys, key_vals)}
        rec.update({k: m[k] for k in
                    ("n", "positive_rate", "brier", "log_loss", "roc_auc",
                     "pr_auc", "precision", "recall", "f1", "ece",
                     "confusion_matrix", "mean_predicted_prob", "n_pos", "n_pred_pos")})
        rec["reliability"] = m["reliability"]
        records.append(rec)
    return records


def dframe(array_of_records: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(array_of_records)
    for c in df.columns:
        if df[c].dropna().map(lambda v: isinstance(v, (list, dict))).any():
            df = df.drop(columns=c)
    return df


def plot_brier_bar(split_metrics: pd.DataFrame, fname: str) -> None:
    df = split_metrics[split_metrics["split"].isin(["val", "test"])].dropna(subset=["brier"])
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    models_order = ["climatology", "persistence", "logistic", "random_forest", "xgboost"]
    for ax, tgt in zip(axes.flat, PUBLIC_TARGETS):
        d = df[df["target"] == tgt]
        x = np.arange(len(models_order)); w = 0.38
        for k, sp in enumerate(("val", "test")):
            vals = [float(d.loc[(d["model"] == m) & (d["split"] == sp), "brier"].iloc[0])
                    if ((d["model"] == m) & (d["split"] == sp)).any() else np.nan
                    for m in models_order]
            ax.bar(x + (k - 0.5) * w, vals, w, label=sp, color="#1f77b4" if sp == "val" else "#ff7f0e")
        ax.set_xticks(x); ax.set_xticklabels(models_order, rotation=30)
        ax.set_title(f"{tgt} — Brier (lower better)")
        ax.legend(fontsize=8)
    fig.savefig(FIGURES_DIR / fname, dpi=130)
    plt.close(fig)


def plot_calibration(preds: pd.DataFrame, targets=PUBLIC_TARGETS,
                     models=("climatology", "persistence", "logistic", "random_forest", "xgboost"),
                     split="val", fname=None) -> None:
    sub = preds[(preds["split"] == split)]
    n = len(targets); ncol = 5
    fig, axes = plt.subplots(n, ncol, figsize=(22, 3.4 * n), constrained_layout=True)
    for i, tgt in enumerate(targets):
        for j, mod in enumerate(models):
            ax = axes[i, j]
            d = sub[(sub["target"] == tgt) & (sub["model"] == mod)]
            if d.empty:
                ax.set_visible(False); continue
            m = compute_metrics(d["observed_label"].to_numpy(), d["probability"].to_numpy())
            rel = m["reliability"]
            mp = [r["bin_mean_pred"] for r in rel]; fq = [r["bin_freq"] for r in rel]
            ax.plot([0, 1], [0, 1], "--", color="grey", lw=1)
            ax.plot(mp, fq, marker="o", ms=3)
            ax.set_title(f"{tgt} · {mod}\nECE={m['ece']:.3f} Brier={m['brier']:.4f}", fontsize=9)
            ax.set_xlim(0, 1); ax.set_ylim(0, 1)
            ax.set_xlabel("predicted"); ax.set_ylabel("observed")
            ax.grid(alpha=0.3)
    fig.savefig(FIGURES_DIR / (fname or f"calibration_{split}.png"), dpi=130)
    plt.close(fig)


def plot_roc_pr(preds: pd.DataFrame, models=("logistic", "random_forest", "xgboost"),
                split="val") -> None:
    from sklearn.metrics import roc_curve, precision_recall_curve
    sub = preds[(preds["split"] == split)]
    fig, axes = plt.subplots(len(PUBLIC_TARGETS), 2, figsize=(14, 3.6 * len(PUBLIC_TARGETS)),
                             constrained_layout=True)
    for i, tgt in enumerate(PUBLIC_TARGETS):
        for j, (kind, curves) in enumerate((("ROC", roc_curve), ("PR", precision_recall_curve))):
            ax = axes[i, j]
            for mod in models:
                d = sub[(sub["target"] == tgt) & (sub["model"] == mod)]
                y = d["observed_label"].to_numpy(); p = d["probability"].to_numpy()
                if len(np.unique(y)) < 2 or len(np.unique(p)) < 2:
                    continue
                if kind == "ROC":
                    fpr, tpr, _ = curves(y, p)
                    ax.plot(fpr, tpr, label=mod)
                else:
                    prec, rec, _ = curves(y, p)
                    ax.plot(rec, prec, label=mod)
            if kind == "ROC":
                ax.plot([0, 1], [0, 1], "--", color="grey")
            ax.set_title(f"{tgt} · {kind} ({split})")
            ax.set_xlabel(kind[0] + "PR" if kind == "ROC" else "Recall")
            ax.set_ylabel("TPR" if kind == "ROC" else "Precision")
            ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.savefig(FIGURES_DIR / f"roc_pr_{split}.png", dpi=130)
    plt.close(fig)


def plot_yearly(preds: pd.DataFrame, fname="yearly_brier.png") -> None:
    """Yearly Brier over all years present in the prediction table (train 15-21, val 22-23, test 24)."""
    sub = preds.groupby(["year", "model", "target"]).apply(
        lambda d: pd.Series({"brier": ((d["probability"] - d["observed_label"]) ** 2).mean()}),
        include_groups=False).reset_index()
    sub["year"] = sub["year"].astype(str)
    models_order = ["climatology", "persistence", "logistic", "random_forest", "xgboost"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 9), constrained_layout=True)
    for ax, tgt in zip(axes.flat, PUBLIC_TARGETS):
        d = sub[sub["target"] == tgt]
        for mod in models_order:
            dd = d[d["model"] == mod]
            if dd.empty:
                continue
            ax.plot(dd["year"], dd["brier"], marker="o", ms=4, label=mod)
        ax.set_title(f"{tgt} — Brier by calendar year")
        ax.legend(fontsize=8); ax.grid(alpha=0.3)
        ax.tick_params(axis="x", rotation=45)
    fig.savefig(FIGURES_DIR / fname, dpi=130)
    plt.close(fig)


def plot_obs_vs_pred(preds: pd.DataFrame, split="val") -> None:
    sub = preds[(preds["split"] == split)]
    agg = sub.groupby(["target", "model"]).apply(
        lambda d: pd.Series({"obs": d["observed_label"].mean(), "pred": d["probability"].mean()}),
        include_groups=False).reset_index()
    n = len(PUBLIC_TARGETS)
    fig, axes = plt.subplots(1, n, figsize=(16, 4), constrained_layout=True)
    for ax, tgt in zip(axes, PUBLIC_TARGETS):
        d = agg[agg["target"] == tgt]
        ax.scatter(d["pred"], d["obs"], s=40)
        ax.plot([0, max(d["pred"].max(), d["obs"].max())] * 1, [0, max(d["pred"].max(), d["obs"].max())], "--", color="grey")
        for _, r in d.iterrows():
            ax.annotate(r["model"], (r["pred"], r["obs"]), fontsize=7)
        ax.set_xlabel("mean predicted"); ax.set_ylabel("observed freq"); ax.set_title(f"{tgt} ({split})")
    fig.savefig(FIGURES_DIR / f"obs_vs_pred_{split}.png", dpi=130)
    plt.close(fig)