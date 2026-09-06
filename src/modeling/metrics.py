"""Probabilistic + classification metrics for Phase F. Sklearn-standard implementations only."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
    roc_auc_score,
)

EPS = 1e-12


def ece(y_true: np.ndarray, y_prob: np.ndarray, nbins: int = 10) -> float:
    """Expected Calibration Error on equal-width bins over [0,1]."""
    y_true = np.asarray(y_true, float)
    y_prob = np.asarray(y_prob, float)
    edges = np.linspace(0.0, 1.0, nbins + 1)
    n = len(y_true)
    if n == 0:
        return float("nan")
    total = 0.0
    for i in range(nbins):
        lo, hi = edges[i], edges[i + 1]
        if i == nbins - 1:
            mask = (y_prob >= lo) & (y_prob <= hi)
        else:
            mask = (y_prob >= lo) & (y_prob < hi)
        cnt = int(mask.sum())
        if cnt == 0:
            continue
        bins = cnt / n
        mean_p = float(y_prob[mask].mean())
        freq = float(y_true[mask].mean())
        total += bins * abs(mean_p - freq)
    return total


def reliability(y_true: np.ndarray, y_prob: np.ndarray, nbins: int = 10) -> list[dict]:
    """Reliability-diagram data: {bin_mean_pred, bin_freq, bin_count, bin_edges}."""
    y_true = np.asarray(y_true, float)
    y_prob = np.asarray(y_prob, float)
    edges = np.linspace(0.0, 1.0, nbins + 1)
    out = []
    for i in range(nbins):
        lo, hi = edges[i], edges[i + 1]
        if i == nbins - 1:
            mask = (y_prob >= lo) & (y_prob <= hi)
        else:
            mask = (y_prob >= lo) & (y_prob < hi)
        cnt = int(mask.sum())
        out.append({
            "bin_edges": [float(lo), float(hi)],
            "bin_count": cnt,
            "bin_mean_pred": float(y_prob[mask].mean()) if cnt else float("nan"),
            "bin_freq": float(y_true[mask].mean()) if cnt else float("nan"),
        })
    return out


def compute_metrics(y_true, y_prob, name: str = "", nbins: int = 10) -> dict:
    y_true = np.asarray(y_true, float)
    y_prob = np.asarray(y_prob, float)
    n = len(y_true)
    out = {"n": int(n), "name": name}

    out["positive_rate"] = float(y_true.mean())
    out["mean_predicted_prob"] = float(y_prob.mean())

    out["brier"] = float(brier_score_loss(y_true, y_prob))
    out["log_loss"] = float(log_loss(y_true, np.clip(y_prob, EPS, 1 - EPS)))

    n_pos = int(y_true.sum())
    n_neg = n - n_pos
    n_pred_pos = int((y_prob >= 0.5).sum())
    n_pred_neg = n - n_pred_pos

    # ROC-AUC and PR-AUC are undefined for constant predictions or a single class.
    if (n_pos >= 1 and n_neg >= 1 and len(np.unique(y_prob)) > 1):
        out["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        out["pr_auc"] = float(average_precision_score(y_true, y_prob))
    else:
        out["roc_auc"] = None
        out["pr_auc"] = None

    y_pred = (y_prob >= 0.5).astype(int).ravel()
    out["precision"] = float(precision_score(y_true, y_pred, zero_division=0))
    out["recall"] = float(recall_score(y_true, y_pred, zero_division=0))
    out["f1"] = float(f1_score(y_true, y_pred, zero_division=0))
    out["confusion_matrix"] = [[int(v) for v in row] for row in
                               confusion_matrix(y_true, y_pred)]
    out["n_pred_pos"] = int(n_pred_pos)
    out["n_pred_neg"] = int(n_pred_neg)
    out["n_pos"] = n_pos
    out["n_neg"] = n_neg
    out["ece"] = float(ece(y_true, y_prob, nbins))
    out["reliability"] = reliability(y_true, y_prob, nbins)
    return out