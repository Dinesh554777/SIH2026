"""Phase H modeling integrity tests (H5-H9).

Run:  python -m pytest tests/test_phase_h_modeling.py -q

Covers: chronological splits, train-only imputation, no test contamination,
feature-group correctness, prediction alignment, freeze integrity, reproducibility.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modeling.common import PROJECT_ROOT, PUBLIC_TARGETS, TARGETS  # noqa: E402
from src.modeling.phase_h import modeling as M  # noqa: E402

FREEZE_H = PROJECT_ROOT / "data" / "processed" / "FREEZE_H.json"


@pytest.fixture(scope="module")
def ph():
    return pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "phase_h_matrix.parquet")


@pytest.fixture(scope="module")
def predictions():
    return M.load_group_predictions()


def test_h_chronological_splits(ph):
    yrs = ph.assign(yr=pd.to_datetime(ph["date"]).dt.year).groupby("split")["yr"] \
        .agg(["min", "max"])
    exp = {"train": (2015, 2021), "val": (2022, 2023), "test": (2024, 2024)}
    for s, (lo, hi) in exp.items():
        assert tuple(int(x) for x in yrs.loc[s].values.tolist()) == (lo, hi), f"{s} wrong"


def test_imputation_fitted_on_train_only(ph):
    imp = M.all_groups_matrix(ph)
    tr = ph[ph["split"] == "train"]
    for f in M.IMPUTED_FEATURES:
        train_median = np.nanmedian(tr[f])
        val_col = imp.loc[imp["split"] == "val", f]
        # any originally-NaN val rows must equal the train median (not val-derived)
        nan_idx = ph[(ph["split"] == "val") & ph[f].isna()].index
        if len(nan_idx):
            assert np.allclose(imp.loc[nan_idx, f], train_median), f"{f} imputed with non-train median"
        test_idx = ph[(ph["split"] == "test") & ph[f].isna()].index
        if len(test_idx):
            assert np.allclose(imp.loc[test_idx, f], train_median), f"{f} test imputed with non-train median"


def test_no_test_contamination_in_freeze(predictions):
    """Group predictions must contain only train+val (no 2024 observed labels used in fitting)."""
    assert predictions["split"].isin(["train", "val"]).all()
    freeze = json.load(open(FREEZE_H, encoding="utf-8"))
    assert freeze["note"].startswith("2024 TEST DATA WAS NOT USED")


def test_freeze_integrity():
    freeze = json.load(open(FREEZE_H, encoding="utf-8"))
    assert freeze["phase"] == "H"
    for tgt in PUBLIC_TARGETS:
        assert tgt in freeze["targets"], f"{tgt} missing from FREEZE_H targets"
    # revival must be the learned candidate; others frozen reference
    assert freeze["targets"]["revival"]["decision"].startswith("CANDIDATE")
    for t in ("onset", "break", "dry_spell"):
        assert freeze["targets"][t]["decision"].startswith("KEEP")
    # group F must not be constructed (no evidence for it)
    assert freeze["groups"]["F"]["constructed"] is False


def test_group_partition(ph):
    import src.modeling.phase_h.groups as G  # noqa: F401
    A = M.group_features(ph, "A")
    assert len(A) == 51
    assert not any(c.startswith(("th_", "sh_", "es_", "sp_")) for c in A)
    for g, pre in (("B", "th_"), ("C", "sh_"), ("D", "es_"), ("E", "sp_")):
        add = [c for c in M.group_features(ph, g) if c.startswith(pre)]
        assert len(add) > 0, f"group {g} has no {pre} features"
        assert set(A).isdisjoint(add)


def test_prediction_alignment(predictions):
    """Group prediction tables must not have duplicate (cell_id, date) per (group,target,model,split)."""
    key = ["date", "cell_id", "target", "model", "split", "group"]
    dups = predictions.duplicated(subset=key)
    assert not dups.any(), f"{int(dups.sum())} duplicated prediction rows"


def test_reproducibility_of_group_features(ph):
    f1 = M.group_features(ph, "B")
    f2 = M.group_features(ph, "B")
    assert f1 == f2


def test_imputation_stats_frozen_consistency():
    """CONFIG.json imputer stats must be consistent across groups for shared (non-new) cols."""
    grp = ["B"]
    cfgs = []
    for g in grp:
        for tgt in TARGETS.values():
            p = PROJECT_ROOT / "models" / "phase_h" / g / tgt / "CONFIG.json"
            cfgs.append(json.load(open(p, encoding="utf-8")))
    stats = {c["target"]: c["imputation"]["statistics"] for c in cfgs}
    # first 51 entries (Group A models) must be identical across targets
    base = stats["onset"][:51]
    for t in TARGETS.values():
        assert stats[t][:51] == base, f"imputation stats differ for {t}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))