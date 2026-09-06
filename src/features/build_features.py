"""Feature engineering for SIH26086 reforecast-style training matrix.

All features at sample date T use ONLY observations <= T (end-of-day T value is
allowed: the advisory fires after the day closes). Climatology-based anomaly
features are fit EXCLUSIVELY on the TRAIN split (2015-2021) — see Phase D
leakage checks L-6.

Feature groups:
  imd_    IMD 0.25 grid (lags, trailing sums, wet/dry-counts, streaks,
              cumulative-JJAS, anomalies vs train climatology)
  chirps_ CHIRPS(0.05-aggregated-to-cell) (values, sums, wet-freq, variability)
  nasa_   NASA POWER 8 atmospheric params, value-at-T + 7-day mean
  oni_    NOAA ONI, last two *released* (>= 45 d after season end) values

Intermediate long tables are cached under data/processed/cache/ to avoid
rebuilding NASA (>90 CSVs) on every run.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.labels import definitions as D  # noqa: E402
from src.data_pipeline_utils import PROCESSED  # noqa: E402
from src.load import read_nasa_csv  # noqa: E402

CACHE = PROCESSED / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

TRAIN_START, TRAIN_END = date(2015, 1, 1), date(2021, 12, 31)
TRAIN_YEARS = list(range(2015, 2022))


# ---------------------------------------------------------------------------
# IMD features
# ---------------------------------------------------------------------------
def _rolling(df: pd.DataFrame, col: str, w: int, fn) -> np.ndarray:
    g = df.groupby("cell_id")[col].rolling(w, min_periods=1)
    return fn(g).reset_index(level=0, drop=True).to_numpy()


def build_imd_features(imd: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    """Long-frame IMD features per (cell_id, date) over 2015-2024 (all days)."""
    df = imd[["cell_id", "date", "rain"]].sort_values(["cell_id", "date"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    r = df["rain"].to_numpy()
    wet1 = (r >= D.WET_DAY_MM).astype(float)
    dry1 = (r < 1.0).astype(float)
    df["imd_rain_t"] = r
    df["imd_wet1"] = wet1

    peaks: dict[str, np.ndarray] = {}
    for w in D.LAG_WINDOWS_DAYS:
        df[f"imd_sum{w}"] = _rolling(df, "rain", w, lambda g: g.sum())
        df[f"imd_wet{w}"] = df.assign(x=wet1).groupby("cell_id")["x"].rolling(
            w, min_periods=1).sum().reset_index(level=0, drop=True).to_numpy()
        df[f"imd_dry{w}"] = df.assign(x=dry1).groupby("cell_id")["x"].rolling(
            w, min_periods=1).sum().reset_index(level=0, drop=True).to_numpy()
    df["imd_rain_lag1"] = df.groupby("cell_id")["rain"].shift(1)
    df["imd_rain_lag3"] = df.groupby("cell_id")["rain"].shift(3)
    df["imd_max3"] = df.groupby("cell_id")["rain"].rolling(
        3, min_periods=1).max().reset_index(level=0, drop=True).to_numpy()

    # streak features (capped, then NaN gap at t omitted by using shift-agg)
    df["imd_days_since_wet"] = df.assign(wet=wet1).groupby("cell_id")["wet"].apply(
        lambda s: s.groupby((~s.astype(bool)).cumsum()).cumcount()).to_numpy().clip(0, 60)
    consec_dry = df.assign(d=dry1).groupby("cell_id")["d"].apply(
        lambda s: s.groupby((s == 0).cumsum()).cumcount()).to_numpy().clip(0, 60)
    df["imd_consec_dry"] = consec_dry

    # cumulative JJAS rain within season
    season = df.copy()
    season["year"] = season["date"].dt.year
    season["jj"] = season["date"].dt.month.isin([6, 7, 8, 9])
    season["cum"] = np.where(season["jj"], season["rain"], 0.0)
    df["imd_cum_jjas"] = season.groupby(["cell_id", "year"])["cum"].cumsum().to_numpy()

    # calendar context
    df["year"] = df["date"].dt.year
    df["doy"] = df["date"].dt.dayofyear
    dseason = (df["date"] - np.datetime64("1970-01-01")).dt.days  # placeholder
    june1 = pd.to_datetime(df["year"].astype(str) + "-06-01")
    df["dseason"] = ((df["date"] - june1).dt.days + 1).where(df["date"] >= june1)
    df.loc[df["date"].dt.month.isin([6, 7, 8, 9]) == False, "dseason"] = np.nan  # noqa: E712
    return df


def train_climatology(imd: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    """Per-cell per-doy TRAIN-only rainfall climatologies for anomaly features."""
    tr = imd[imd["cell_id"].isin(cells.cell_id)].copy()
    tr["date"] = pd.to_datetime(tr["date"])
    tr["year"] = tr["date"].dt.year
    tr = tr[tr["year"].isin(TRAIN_YEARS)]
    tr["doy"] = tr["date"].dt.dayofyear
    out = tr.groupby(["cell_id", "doy"])["rain"].agg(["mean"]).reset_index()
    # Window climatologies: mean of S7/S14/S30 around each doy (train-only)
    feat = build_imd_features(tr, cells)
    for w in (7, 14, 30):
        cl = feat.groupby(["cell_id", "doy"])[f"imd_sum{w}"].mean().reset_index() \
            .rename(columns={f"imd_sum{w}": f"clim_sum{w}"})
        out = out.merge(cl, on=["cell_id", "doy"], how="left")
    return out.rename(columns={"mean": "clim_daily"})


def add_imd_anomalies(feat: pd.DataFrame, clim: pd.DataFrame) -> pd.DataFrame:
    m = feat.merge(clim, on=["cell_id", "doy"], how="left")
    for w in (7, 14, 30):
        m[f"imd_anom{w}"] = m[f"imd_sum{w}"] - m[f"clim_sum{w}"]
    m["imd_anom_t"] = m["imd_rain_t"] - m["clim_daily"]
    m = m.drop(columns=[c for c in ("clim_daily", "clim_sum7", "clim_sum14",
                                    "clim_sum30") if c in m.columns])
    return m


# ---------------------------------------------------------------------------
# CHIRPS features
# ---------------------------------------------------------------------------
def build_chirps_features(chirps: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    df = chirps[chirps["cell_id"].isin(cells.cell_id)].sort_values(
        ["cell_id", "date"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    for w in (7, 14):
        df[f"chirps_sum{w}"] = df.groupby("cell_id")["chirps_rain"].rolling(
            w, min_periods=1).sum().reset_index(level=0, drop=True).to_numpy()
    w = (df["chirps_rain"] >= D.WET_DAY_MM).astype(float)
    df["chirps_wet7"] = df.assign(x=w).groupby("cell_id")["x"].rolling(
        7, min_periods=1).sum().reset_index(level=0, drop=True).to_numpy()
    df["chirps_lag1"] = df.groupby("cell_id")["chirps_rain"].shift(1)
    return df[["cell_id", "date", "chirps_rain",
               "chirps_lag1", "chirps_sum7", "chirps_sum14", "chirps_wet7"]]


# ---------------------------------------------------------------------------
# NASA features (eventual cache)
# ---------------------------------------------------------------------------
def build_nasa_features(cells: pd.DataFrame,
                        params: list[str] | None = None) -> pd.DataFrame:
    params = params or D.NASA_FEATURE_PARAMS
    cache_path = CACHE / "nasa_features.parquet"
    if cache_path.exists():
        return pd.read_parquet(cache_path)
    raw_root = Path(str(Path(__file__).resolve().parents[2])) / "data" / "raw" / "nasa"
    param_dfs = {}
    for param in params:
        pts = []
        for year in range(2015, 2025):
            for band in ("b1", "b2"):
                p = raw_root / f"nasa_power_daily_{param}_{band}_{year}.csv"
                pts.append(read_nasa_csv(p, usecols=["LAT", "LON", "YEAR", "DOY", param]))
        df = pd.concat(pts, ignore_index=True)
        df = df[df[param] > -999.0]
        df["date"] = (pd.to_datetime(df["YEAR"].astype(int).astype(str), format="%Y")
                      + pd.to_timedelta(df["DOY"].astype(int) - 1, unit="D"))
        df = df.set_index(["LAT", "LON"]).sort_index()
        u_lat = np.unique(df.index.get_level_values(0).to_numpy(float))
        u_lon = np.unique(df.index.get_level_values(1).to_numpy(float))
        param_dfs[param] = (df, u_lat, u_lon)
    # nearest NASA point per cell (one pass over cells, not over grid)
    rows = []
    for _, cell in cells.iterrows():
        for param, (gdf, u_lat, u_lon) in param_dfs.items():
            il = int(np.argmin(np.abs(u_lat - cell.lat)))
            io = int(np.argmin(np.abs(u_lon - cell.lon)))
            s = gdf.loc[(u_lat[il], u_lon[io])].set_index("date")[param].sort_index()
            base = pd.DataFrame({"date": s.index.to_numpy(),
                                 f"nasa_{param}_t": s.to_numpy()})
            base[f"nasa_{param}_a7"] = s.rolling(7, min_periods=1).mean().to_numpy()
            base["cell_id"] = cell.cell_id
            rows.append(base)
    out = pd.concat(rows, ignore_index=True)
    out.to_parquet(cache_path)
    return out


# ---------------------------------------------------------------------------
# Compose
# ---------------------------------------------------------------------------
def build_feature_matrix(imd: pd.DataFrame, cells: pd.DataFrame,
                         daily_labels: pd.DataFrame,
                         chirps: pd.DataFrame | None = None,
                         nasa: pd.DataFrame | None = None,
                         oni: pd.DataFrame | None = None) -> pd.DataFrame:
    fidx = build_imd_features(imd, cells)
    clim = train_climatology(imd, cells)
    fidx = add_imd_anomalies(fidx, clim)

    out = daily_labels.drop(columns=["rain_mm"]).copy()
    out["date"] = pd.to_datetime(out["date"])
    fidx = fidx.drop(columns=[c for c in ("rain", "year", "doy", "dseason", "valid")
                              if c in fidx.columns])
    out = out.merge(fidx, on=["cell_id", "date"], how="left")

    if chirps is not None:
        out = out.merge(build_chirps_features(chirps, cells), on=["cell_id", "date"],
                        how="left")
    if nasa is None:
        nasa = build_nasa_features(cells)
    pv = nasa.pivot_table(index=["cell_id", "date"], aggfunc="first").reset_index()
    out = out.merge(pv, on=["cell_id", "date"], how="left")

    if oni is None:
        from src.load import asof_oni, oni_series
        oni = oni_series()
    o = asof_oni(oni, [str(d) for d in out["date"].dt.date.unique()])
    out = out.merge(o, left_on="date", right_on="date", how="left")

    out = out.merge(cells[["cell_id", "lat", "lon", "bbox_guess", "admin_mapping"]],
                    on="cell_id", how="left")
    return out