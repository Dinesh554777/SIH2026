"""Phase H feature-matrix integrity tests (Steps 4, 11).

Run:  python -m pytest tests/test_phase_h_features.py -q

Covers: row identity, ordering, duplicates, causality, train-only climatology,
no target leakage, spatial row-preservation, determinism, chronological splits,
and group-partition correctness.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modeling.common import MATRIX_PATH, feature_columns  # noqa: E402
from src.modeling.phase_h import features as F  # noqa: E402
from src.modeling.phase_h import groups as G  # noqa: E402

NEW_PREFIXES = ("th_", "sh_", "es_", "sp_")


@pytest.fixture(scope="module")
def df():
    return pd.read_parquet(MATRIX_PATH)


@pytest.fixture(scope="module")
def cells(df):
    return df[["cell_id", "lat", "lon"]].drop_duplicates()


@pytest.fixture(scope="module")
def res(df, cells):
    return G.build_all_groups(df, cells)


@pytest.fixture(scope="module")
def ph(df, res):
    return G.assemble_matrix(df, res)


def test1_row_identity(ph, df):
    o = df[["cell_id", "date"]].reset_index(drop=True)
    p = ph[["cell_id", "date"]].reset_index(drop=True)
    assert o.equals(p), "(cell_id, date) identity differs"


def test2_ordering(ph, df):
    assert ph.sort_values(["cell_id", "date"]).reset_index(drop=True)[
        ["cell_id", "date"]].equals(ph[["cell_id", "date"]].reset_index(drop=True)), \
        "not sorted by (cell_id, date)"


def test3_no_duplicate_rows(ph):
    assert not ph[["cell_id", "date"]].duplicated().any(), "duplicate (cell_id, date)"


def test4_temporal_causal_manual():
    """Rolling/streak features at t use only info at t and earlier."""
    np.random.seed(0)
    n = 40
    rain = np.random.rand(n) * 10
    sub = pd.DataFrame({
        "cell_id": ["C0"] * n, "year": [2020] * n,
        "dseason": np.arange(1, n + 1), "date": pd.date_range("2020-06-01", periods=n),
        "imd_rain_t": rain,
    })
    temp = F.build_temporal(sub)
    for i in range(3, n):
        lo = max(0, i - 4)
        assert abs(temp["th_sum5"].iloc[i] - rain[lo:i + 1].sum()) < 1e-9 + 1e-6 * abs(rain[lo:i + 1].sum())
    # streak requires strict past (shift(1)); today's own wetness enters only via rolling not streak
    pat = (rain >= 1.0).astype(int)
    # manually recompute wet streak ending yesterday for a middle row
    for i in [7, 8, 20, 21, 33]:
        # number of consecutive wet days in days [i-1, i-2, ...) (yesterday-backward)
        cnt = 0
        j = i - 1
        while j >= 0 and pat[j] == 1:
            cnt += 1
            j -= 1
        assert temp["th_wet_streak"].iloc[i] == cnt, f"wet streak mismatch at {i}"

    # th_accel: (S3_t - S3_{t-1}) within same (cell, year); reset at boundary
    s3 = pd.Series(rain).rolling(3, min_periods=1).sum().to_numpy()
    for i in range(1, n):
        assert abs(temp["th_accel"].iloc[i] - (s3[i] - s3[i - 1])) < 1e-9


def test5_climatology_train_only(df):
    train = df[df["split"] == "train"]
    val = df[df["split"] == "val"]
    test = df[df["split"] == "test"]
    m_tr, s_tr, pool_tr, onset_tr = F.build_doy_climatology(train)
    # build a climatology from ALL data and confirm frozen-onset same only via train subset
    assert set(pool_tr.index.get_level_values("doy").unique()) == set(train["doy"].unique())
    assert {d: pool_tr[d].size for d in pool_tr.index} == {d: int((train["doy"] == d).sum()) for d in pool_tr.index}, \
        "pooled ECDF must contain ONLY training observations"
    # val/test doy values must not add any pool entries beyond train doy set
    assert set(val["doy"].unique()) <= set(train["doy"].unique())
    assert set(test["doy"].unique()) <= set(train["doy"].unique())
    # climatological onset is a single deterministic value from train
    assert isinstance(onset_tr, (int, np.integer))


def test6_no_target_leakage(df, ph):
    tgt = [c for c in df.columns if "_active" in c]
    evd = [c for c in df.columns if c.endswith("_date")]
    # event-date columns must never be predictors (Group A) nor referenced by H1-H4
    assert not any(c in feature_columns(df) for c in evd), \
        f"event-date column leaked into Group A: {evd}"
    rep = [c for c in ph.columns if c.startswith(NEW_PREFIXES)]
    for c in rep:
        for t in tgt:
            assert not ph[c].equals(ph[t]), f"{c} equals target column {t}"
        for ed in evd:
            assert not ph[c].equals(ph[ed]), f"{c} equals event-date column {ed}"
    # H3/H1 derive strictly from rainfall; verify no label/event-date column name
    # appears in the builder implementations
    import inspect
    src = inspect.getsource(F.build_temporal) + inspect.getsource(F.event_state_features)
    banned_names = [c for c in df.columns if "_active" in c or c.endswith("_date")]
    for banned in banned_names:
        assert banned not in src, f"feature builder references {banned}"
    # labels remain intact as dtype numeric
    for t in tgt:
        assert ph[t].dtype.kind in "idf"


def test7_spatial_row_preserved(df, ph, res):
    sp = res["frames"]["spatial"]
    assert len(sp) == len(df)
    assert (ph[["cell_id", "date"]].reset_index(drop=True) ==
            df[["cell_id", "date"]].reset_index(drop=True)).all().all()
    # no row added/lost by spatial pivot
    assert sp.shape[0] == df.shape[0]


def test8_deterministic_rebuild(df, cells):
    r1 = G.build_all_groups(df, cells)
    r2 = G.build_all_groups(df, cells)
    for k in r1["frames"]:
        a = r1["frames"][k].to_numpy(); b = r2["frames"][k].to_numpy()
        if a.dtype.kind == "f":
            assert np.allclose(a, b, rtol=0, atol=0, equal_nan=True), f"{k} not deterministic"
        else:
            assert (a == b).all(), f"{k} not deterministic"


def test9_chronological_splits(df, ph):
    yrs = ph.assign(yr=pd.to_datetime(ph["date"]).dt.year).groupby("split")["yr"] \
        .agg(["min", "max"])
    exp = {"train": (2015, 2021), "val": (2022, 2023), "test": (2024, 2024)}
    for s, (lo, hi) in exp.items():
        assert tuple(int(x) for x in yrs.loc[s].values.tolist()) == (lo, hi), f"{s} years wrong"
    assert not ph["split"].isna().any()


def test10_group_partition(res, df):
    A = set(res["A_group"])
    B = set(res["B_temporal"]) - A
    C = set(res["C_seasonal"]) - A
    D = set(res["D_event_state"]) - A
    E = set(res["E_spatial"]) - A
    assert len(A) == 51
    assert all(c.startswith("th_") for c in B)
    assert all(c.startswith("sh_") for c in C)
    assert all(c.startswith("es_") for c in D)
    assert all(c.startswith("sp_") for c in E)
    assert not (B & C | C & D | D & E | B & E | B & D | C & E), "group overlap"
    # group A must contain NO new prefix
    assert not any(c.startswith(NEW_PREFIXES) for c in A)


def test11_no_future_info_in_matrix(ph):
    """Spot-check a temporal feature value depends only on same/earlier rows (year-aware)."""
    sub = ph[ph["cell_id"] == ph["cell_id"].iloc[0]].sort_values("date").reset_index(drop=True)
    rain = sub["imd_rain_t"].to_numpy()
    years = sub["year"].to_numpy()
    for i in range(3, len(sub)):
        # reset window at year boundary (rolling is grouped by cell, year)
        j = i
        while j > 0 and years[j - 1] == years[i]:
            j -= 1
        lo = max(j, i - 4)
        assert abs(sub["th_sum5"].iloc[i] - rain[lo:i + 1].sum()) < 1e-9


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))