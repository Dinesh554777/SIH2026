"""Phase H feature representations (H1 temporal, H2 seasonal, H3 event-state, H4 spatial).

ALL new features are causal (past-only or same-day observed nowcast). Any climatology
is fit on TRAINING (2015-2021) only. Event-state features derive from IMD rainfall
observations ONLY (never from target labels) -> no target leakage by construction.

The training matrix is pre-sorted by (cell_id, date). All builders return frames
with the SAME row order as the input df.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.modeling.common import MATRIX_PATH, PROJECT_ROOT

PH_OUT = PROJECT_ROOT / "data" / "processed" / "phase_h_matrix.parquet"
GRID_STEP = 0.25


def _block_streaks(cells: np.ndarray, years: np.ndarray, flag: np.ndarray) -> np.ndarray:
    """Consecutive run-length of flag==1 (wet) and flag==0 (dry), reset at (cell, year)."""
    n = len(cells)
    wet = np.zeros(n, dtype=int)
    dry = np.zeros(n, dtype=int)
    cw = cd = 0
    for i in range(n):
        if i > 0 and (cells[i] != cells[i - 1] or years[i] != years[i - 1]):
            cw = cd = 0
        if flag[i] == 1:
            cw += 1; cd = 0
        else:
            cd += 1; cw = 0
        wet[i] = cw; dry[i] = cd
    return wet, dry


# ---------------------------------------------------------------- H1 temporal
def build_temporal(df: pd.DataFrame) -> pd.DataFrame:
    """Rolling sums/means/std/cv/counts/streaks over IMD rain. Causal. th_ prefix."""
    x = df[["cell_id", "year", "dseason", "imd_rain_t"]].copy()
    g = x.groupby(["cell_id", "year"])["imd_rain_t"]
    wet = (x["imd_rain_t"] >= 1.0).astype(int)
    gw = x.assign(_wet=wet).groupby(["cell_id", "year"])["_wet"]

    cols = {}
    for w in (5, 10, 21):
        cols[f"th_sum{w}"] = g.transform(lambda s: s.rolling(w, min_periods=1).sum())
    for w in (7, 14):
        cols[f"th_rmean{w}"] = g.transform(lambda s: s.rolling(w, min_periods=1).mean())
        cols[f"th_rstd{w}"] = g.transform(lambda s: s.rolling(w, min_periods=1).std())
    m7 = cols["th_rmean7"]
    s7 = cols["th_rstd7"].replace(0, np.nan)
    cols["th_cv7"] = (s7 / m7).fillna(0.0)
    cols["th_wetcount7"] = gw.transform(lambda s: s.rolling(7, min_periods=1).sum())
    cols["th_wetcount14"] = gw.transform(lambda s: s.rolling(14, min_periods=1).sum())
    # streaks ending YESTERDAY (strictly past)
    wp = gw.shift(1).fillna(0).astype(int)
    wr, dr = _block_streaks(x["cell_id"].to_numpy(), x["year"].to_numpy(), wp.to_numpy())
    cols["th_wet_streak"] = wr
    cols["th_dry_streak"] = dr
    # acceleration (3d change)
    s3 = g.transform(lambda s: s.rolling(3, min_periods=1).sum()).to_numpy()
    s3prev = np.r_[np.nan, s3[:-1]]
    starts = np.zeros(len(x), dtype=bool)
    starts[1:] = (x["cell_id"].to_numpy()[1:] != x["cell_id"].to_numpy()[:-1]) | \
                 (x["year"].to_numpy()[1:] != x["year"].to_numpy()[:-1])
    s3prev = np.where(starts, np.nan, s3prev)
    cols["th_accel"] = np.where(np.isnan(s3prev), s3, s3 - s3prev)

    out = pd.DataFrame(cols)
    out.insert(0, "cell_id", x["cell_id"].to_numpy())
    return out


# ---------------------------------------------------------------- H2 seasonal
def build_doy_climatology(train: pd.DataFrame) -> tuple[pd.Series, pd.Series, pd.Series, int]:
    """Doy-mean/std (of IMD rain, TRAIN only) + per-doy pooled rain values + clim onset.

    Returns:
      mean:   doy -> train-mean daily rain
      std:    doy -> train-std daily rain
      pooled: doy -> sorted train pool of daily rainfall (for ECDF percentile)
      onset_doy: climatological onset doy (rainfall-only S3>=20, train only)
    """
    mean = train.groupby("doy")["imd_rain_t"].mean()
    std = train.groupby("doy")["imd_rain_t"].std()
    pooled = train.groupby("doy")["imd_rain_t"].apply(
        lambda s: np.sort(s.to_numpy()))
    # S3 from train daily rain, averaged by dseason (over all cells & years)
    train_s = train.sort_values(["cell_id", "year", "dseason"])
    tr3 = train_s.groupby(["cell_id", "year"])["imd_rain_t"] \
        .transform(lambda s: s.rolling(3, min_periods=3).sum())
    s3_by_dseason = pd.DataFrame({"dseason": train_s["dseason"].to_numpy(),
                                  "s3": tr3.to_numpy()}) \
        .groupby("dseason")["s3"].mean()
    onset_dseason = int(s3_by_dseason[s3_by_dseason >= 20.0].idxmax()) \
        if (s3_by_dseason >= 20.0).any() else 122
    onset_doy = 151 + onset_dseason
    return mean.astype(float), std.astype(float), pooled, onset_doy


def _pooled_pctile(pool: np.ndarray, value: float) -> float:
    """Empirical percentile of `value` within a train-only pooled sample."""
    if pool.size == 0:
        return 0.5
    return float(np.mean(pool <= value))


def seasonal_features(df: pd.DataFrame, clim_mean: pd.Series, clim_std: pd.Series,
                      clim_pooled: pd.Series, onset_clim_doy: int) -> pd.DataFrame:
    doy = df["doy"].to_numpy()
    dseason = df["dseason"].to_numpy()
    out = pd.DataFrame(index=df.index)
    out["sh_month"] = (np.clip(doy - 151, 0, 122) // 31 + 6).astype(int)
    out["sh_norm_pos"] = dseason / 122.0
    m = clim_mean.reindex(doy).to_numpy()
    s = clim_std.reindex(doy).to_numpy()
    rain = df["imd_rain_t"].to_numpy()
    z = (rain - m) / s
    out["sh_z"] = np.where(np.isfinite(z), z, 0.0)
    pools = clim_pooled.reindex(doy).to_numpy()
    out["sh_clim_pctile"] = [_pooled_pctile(p, r) for p, r in zip(pools, rain)]
    out["sh_onset_prox"] = onset_clim_doy - doy
    out["sh_peak_prox"] = (152 + 61) - doy
    return out


# ---------------------------------------------------------------- H3 event-state
def event_state_features(df: pd.DataFrame) -> pd.DataFrame:
    """State variables from IMD rainfall (causal). es_ prefix."""
    x = df[["cell_id", "year", "dseason", "imd_rain_t"]].copy()
    g = x.groupby(["cell_id", "year"])["imd_rain_t"]
    wet = (x["imd_rain_t"] >= 1.0).astype(int)
    gw = x.assign(_wet=wet).groupby(["cell_id", "year"])["_wet"]
    wp = gw.shift(1).fillna(0).astype(int)
    wdur, ddur = _block_streaks(x["cell_id"].to_numpy(), x["year"].to_numpy(), wp.to_numpy())

    cols = {}
    cols["es_wet_today"] = wet
    cols["es_wet_yest"] = gw.shift(1).fillna(0).astype(int)
    cols["es_wet_2d"] = gw.shift(2).fillna(0).astype(int)
    cols["es_wet_days7"] = gw.transform(lambda s: s.rolling(7, min_periods=1).sum())
    cols["es_wet_days14"] = gw.transform(lambda s: s.rolling(14, min_periods=1).sum())
    cols["es_wet_duration"] = wdur
    cols["es_dry_duration"] = ddur
    m3 = g.transform(lambda s: s.rolling(3, min_periods=1).mean())
    m7 = g.transform(lambda s: s.rolling(7, min_periods=1).mean())
    cols["es_regime"] = np.select([m3 >= 2.5, m7 < 1.5], [1, -1], default=0)
    out = pd.DataFrame(cols)
    out.insert(0, "cell_id", x["cell_id"].to_numpy())
    return out


def build_cum_climatology(train: pd.DataFrame) -> pd.Series:
    """Mean cumulative JJAS IMD rain per doy on TRAIN only."""
    return train.groupby("doy")["imd_cum_jjas"].mean()


def add_deficit(df: pd.DataFrame, train_cum_doy: pd.Series) -> pd.DataFrame:
    """es_rain_deficit: cumulative rain minus train-only expected cumulative (per doy)."""
    exp = train_cum_doy.reindex(df["doy"]).to_numpy()
    deficit = df["imd_cum_jjas"].to_numpy() - exp
    return pd.DataFrame({"cell_id": df["cell_id"].to_numpy(),
                         "es_rain_deficit": deficit})


# ---------------------------------------------------------------- H4 spatial
def build_neighbor_map(cells: pd.DataFrame) -> dict[str, list[str]]:
    lat = cells["lat"].to_numpy(); lon = cells["lon"].to_numpy()
    ids = cells["cell_id"].to_numpy()
    nmap = {}
    for i, cid in enumerate(ids):
        cand = []
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                if di == 0 and dj == 0:
                    continue
                m = np.isclose(lat, lat[i] + di * GRID_STEP, atol=1e-3) & \
                    np.isclose(lon, lon[i] + dj * GRID_STEP, atol=1e-3)
                if m.any():
                    cand.append(ids[np.argwhere(m).ravel()[0]])
        nmap[cid] = cand
    return nmap


def build_neighbor_features(df: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    """Same-date spatial context (8-neighbour) sp_ prefix, same row order as df."""
    nmap = build_neighbor_map(cells)
    cell_ids = cells["cell_id"].tolist()
    piv = df.pivot_table(index="date", columns="cell_id", values="imd_rain_t")

    fc = ["sp_mean", "sp_max", "sp_min", "sp_wetfrac", "sp_grad"]
    frame = {f: np.full((len(piv), len(cell_ids)), np.nan) for f in fc}
    for ci, cid in enumerate(cell_ids):
        nb = [c for c in nmap.get(cid, []) if c in piv.columns]
        if not nb or cid not in piv.columns:
            continue
        nbm = piv[nb].to_numpy()
        sub = piv[cid].to_numpy()
        frame["sp_mean"][:, ci] = np.nanmean(nbm, axis=1)
        frame["sp_max"][:, ci] = np.nanmax(nbm, axis=1)
        frame["sp_min"][:, ci] = np.nanmin(nbm, axis=1)
        frame["sp_wetfrac"][:, ci] = np.nanmean(nbm >= 1.0, axis=1)
        frame["sp_grad"][:, ci] = sub - np.nanmean(nbm, axis=1)
    # lag1: previous date's neighbor-mean, reset at season (year) boundary per cell.
    # piv.index is chronological; same calendar year = same monsoon season (JJAS only).
    prev_year = np.array([pd.Timestamp(p).year for p in piv.index])
    same_as_prev = np.r_[False, prev_year[1:] == prev_year[:-1]]
    mlag = np.full_like(frame["sp_mean"], np.nan)
    mlag[1:] = np.where(same_as_prev[1:, None], frame["sp_mean"][:-1], np.nan)

    # map pivot (date, cell) back to df rows (df is sorted by cell,date)
    dmap = {d: i for i, d in enumerate(piv.index)}
    cmap = {c: i for i, c in enumerate(cell_ids)}
    di = np.array([dmap.get(d, -1) for d in df["date"]])
    ci = np.array([cmap.get(c, -1) for c in df["cell_id"]])
    valid = (di >= 0) & (ci >= 0)
    out = pd.DataFrame({"cell_id": df["cell_id"].to_numpy()})
    for f in fc:
        arr = np.full(len(df), np.nan)
        arr[valid] = frame[f][di[valid], ci[valid]]
        out[f] = arr
    arr = np.full(len(df), np.nan)
    arr[valid] = mlag[di[valid], ci[valid]]
    out["sp_mean_lag1"] = arr
    return out