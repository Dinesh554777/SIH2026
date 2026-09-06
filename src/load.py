"""Loaders + pilot cell-grid definition for SIH26086 labeling/feature phase.

The pilot domain is the union of the three state bounding boxes in
config/project.yaml (Tamil Nadu, Maharashtra, Karnataka). Spatial units are IMD
0.25-deg grid cells WITHIN that domain, identified by cell_id = "{lat:.2f}_{lon:.2f}".

Administrative mapping (state/district/block) is NOT asserted: the config
explicitly marks block boundaries as VERIFY_FROM_OFFICIAL_GIS. Cell rows carry
`bbox_guess` (which state box the cell falls in) purely as context, and
`admin_mapping = "PENDING_OFFICIAL_GIS"` until official GIS is ingested.

Cell validity filter (documented, conservative, reproducible):
  keep cell iff (a) >= 90% of all days 2015-2024 have valid IMD (not -999) and
  (b) its 10-year record contains at least 1% wet days (>=1 mm). Criterion (b)
  drops near-empty sea/desert cells while never touching wet-region cells.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_pipeline_utils import ROOT, RAW  # noqa: E402

BANDS_IN = ("TN", "MH", "KA")
BOXES = [
    (10.0, 13.5, 76.2, 80.4, "TN"),
    (17.5, 19.5, 73.2, 75.0, "MH"),
    (11.5, 12.6, 76.0, 77.2, "KA"),
]
VALID_FRAC = 0.90      # min fraction of non-missing IMD days
MIN_WET_FRAC = 0.01    # min fraction of wet days (>=1 mm)


def imd_series() -> pd.DataFrame:
    """Return long-format IMD daily rainfall for the pilot domain.

    columns: cell_id, lat, lon, date, rain(mm), valid(bool). Missing (-999)
    becomes NaN; `valid` flags present data.
    """
    import netCDF4 as nc
    from cftime import num2date

    domain_rows, domain_cols = None, None
    blocks = []
    for year in range(2015, 2025):
        ds = nc.Dataset(RAW / "imd" / f"ind{year}_rfp25.nc")
        lat = ds.variables["LATITUDE"][:].astype(float)
        lon = ds.variables["LONGITUDE"][:].astype(float)
        rain = np.ma.filled(ds.variables["RAINFALL"][:], np.nan).astype(float)
        las, los = np.meshgrid(lat, lon, indexing="ij")
        dmask = (((las >= 10.0) & (las <= 13.5) & (los >= 76.2) & (los <= 80.4))
                 | ((las >= 17.5) & (las <= 19.5) & (los >= 73.2) & (los <= 75.0))
                 | ((las >= 11.5) & (las <= 12.6) & (los >= 76.0) & (los <= 77.2)))
        li, lo = np.where(dmask)
        li = np.unique(li)
        lo = np.unique(lo)
        if domain_rows is None:
            domain_rows, domain_cols = li, lo
        else:
            domain_rows = np.intersect1d(domain_rows, li)
            domain_cols = np.intersect1d(domain_cols, lo)
        sub = rain[:, domain_rows[:, None], domain_cols[None, :]]
        tt = num2date(ds.variables["TIME"][:], ds.variables["TIME"].units,
                      calendar=getattr(ds.variables["TIME"], "calendar", "standard"))
        dates = [str(x)[:10] for x in tt]
        for r, ilat in enumerate(domain_rows):
            for c, ilon in enumerate(domain_cols):
                blocks.append(pd.DataFrame({
                    "lat": lat[ilat], "lon": lon[ilon],
                    "date": dates, "rain": sub[:, r, c],
                }))
        ds.close()
    df = pd.concat(blocks, ignore_index=True)
    df["valid"] = df["rain"].notna()
    df["cell_id"] = (df["lat"].round(2).astype(str) + "_"
                     + df["lon"].round(2).astype(str))
    return df[["cell_id", "lat", "lon", "date", "rain", "valid"]]


def select_pilot_cells(imd: pd.DataFrame) -> pd.DataFrame:
    """Validity filter -> final cell grid with bbox_guess + pending admin mapping."""
    g = imd.groupby("cell_id").agg(
        lat=("lat", "first"), lon=("lon", "first"),
        valid_frac=("valid", "mean"), wet_frac=("rain", lambda s: ((s >= 1.0)).mean()),
    )
    g = g[(g["valid_frac"] >= VALID_FRAC) & (g["wet_frac"] >= MIN_WET_FRAC)].copy()
    tags = []
    for _, row in g.iterrows():
        t = [b for (mn, mx, wn, wx, b) in BOXES
             if mn <= row.lat <= mx and wn <= row.lon <= wx]
        tags.append(";".join(t))
    g["bbox_guess"] = tags
    g = g[g["bbox_guess"] != ""]  # strictly inside at least one state box
    g["admin_mapping"] = "PENDING_OFFICIAL_GIS"
    g = g.reset_index().rename(columns={"index": "cell_id"})
    g = g.sort_values(["lat", "lon"]).reset_index(drop=True)
    return g[["cell_id", "lat", "lon", "bbox_guess", "admin_mapping"]]


def chirps_cell_series(cells: pd.DataFrame) -> pd.DataFrame:
    """Aggregate CHIRPS 0.05 -> IMD cell footprint (mean over pixels within
    +-CELL_HALF_WIDTH_DEG of the cell centre), long format per cell per day.

    columns: cell_id, date, chirps_rain(mm), valid(bool). -9999 pixels excluded.
    """
    import xarray as xr

    files = sorted((RAW / "chirps").glob("chirps_v3.0_rnl_*_pilot.nc"))
    parts = [xr.open_dataset(p)["precip"] for p in files]
    ds = xr.concat(parts, dim="time")
    ch_lat = ds.lat.values.astype(float)
    ch_lon = ds.lon.values.astype(float)
    dates = np.array([str(x)[:10] for x in ds.time.values], dtype="datetime64[D]")

    records = []
    for _, row in cells.iterrows():
        dl = np.abs(ch_lon - row.lon)
        db = np.abs(ch_lat - row.lat)
        ri = np.argwhere(db <= 0.125).ravel()
        ci = np.argwhere(dl <= 0.125).ravel()
        a = ds.isel(lat=ri.tolist(), lon=ci.tolist()).values  # (days, r, c)
        a = np.where(a == -9999.0, np.nan, a)
        perday = np.nanmean(a.reshape(len(dates), -1), axis=1)  # NaN if all-fill
        records.append(pd.DataFrame({
            "cell_id": row.cell_id, "date": dates.astype("datetime64[D]"),
            "chirps_rain": perday,
        }))
    df = pd.concat(records, ignore_index=True)
    df["valid"] = df["chirps_rain"].notna()
    return df


def read_nasa_csv(path: Path, usecols: list[str] | None = None) -> pd.DataFrame:
    """Read a NASA POWER CSV, skipping the '-BEGIN HEADER-' block robustly."""
    with open(path, encoding="utf-8-sig") as f:
        lines = f.readlines()
    end = next(i for i, l in enumerate(lines)
               if l.strip().startswith("-END HEADER-"))
    return pd.read_csv(path, skiprows=end + 1, encoding="utf-8-sig",
                       usecols=usecols)


def nasa_cell_features(cells: pd.DataFrame, params: list[str]) -> pd.DataFrame:
    """Nearest NASA POWER grid point per cell -> daily value per param.

    Returns long frame columns: cell_id, date, param, value. -999 masked to NaN.
    """
    frames = []
    for param in params:
        pts = []
        for year in range(2015, 2025):
            sub = []
            for band in ("b1", "b2"):
                p = RAW / "nasa" / f"nasa_power_daily_{param}_{band}_{year}.csv"
                sub.append(read_nasa_csv(p))
            yy = pd.concat(sub, ignore_index=True)
            pts.append(yy)
        df = pd.concat(pts, ignore_index=True)
        df = df[(df[param] > -999.0)]  # mask -999 fill
        df["date"] = (pd.to_datetime(df["YEAR"].astype(int).astype(str), format="%Y")
                      + pd.to_timedelta(df["DOY"].astype(int) - 1, unit="D"))
        df = df[["LAT", "LON", "date", param]]
        for _, row in cells.iterrows():
            k = ((df["LAT"] - row.lat).abs().idxmin())
            v = df[(df["LAT"] == df.loc[k, "LAT"]) & (df["LON"] == df.loc[k, "LON"])]
            f = v[["date", param]].rename(columns={param: "value"})
            f["cell_id"] = row.cell_id
            f["param"] = param
            frames.append(f)
    return pd.concat(frames, ignore_index=True)


def oni_series() -> pd.DataFrame:
    """ONI v6 with availability dates (SEAS end + 45-day release buffer).

    Returns columns: season, end_date(date), release_date(date), oni(C, anomaly).
    Feature code may only use rows with release_date <= as-of date (lag>=1 season).
    """
    txt = (RAW / "noaa" / "oni.ascii.txt").read_text(encoding="utf-8")
    rows = []
    for line in txt.splitlines():
        parts = line.split()
        if len(parts) != 4 or not parts[0].isupper():
            continue
        seas, yr, total, anom = parts
        try:
            year = int(yr)
            oni = float(anom)
        except ValueError:
            continue
        # Season = 3 CONSECUTIVE months in canonical order (cyclic): find the
        # unique start position p with canon[p]==seas[0] and canon[(p+1)%12]==seas[1]
        # (disambiguates the duplicate letters J/M/A by their follower).
        canon = "JFMAMJJASOND"
        cand = [i for i in range(12) if canon[i] == seas[0]
                and canon[(i + 1) % 12] == seas[1]]
        if len(cand) != 1:
            continue
        p = cand[0]
        p2 = p + 2                        # end position, possibly wrapped to Jan
        end = date(year + (1 if p2 == 12 else 0), (p2 % 12) + 1, 28)
        rows.append({"season": seas, "end_date": end, "oni": oni})
    df = pd.DataFrame(rows).sort_values("end_date").reset_index(drop=True)
    df["end_date"] = pd.to_datetime(df["end_date"])
    df["release_date"] = df["end_date"] + pd.Timedelta(days=45)
    return df


def asof_oni(oni: pd.DataFrame, dates: list[str]) -> pd.DataFrame:
    """For each as-of date, the last two ONI observations already released.

    Returns per-date: oni_1 (latest released), oni_2 (previous released).
    """
    rel = oni[["release_date", "oni"]].sort_values("release_date").reset_index(drop=True)
    out = []
    for d in np.array(dates, dtype="datetime64[D]"):
        m = rel["release_date"] <= pd.Timestamp(d)
        if m.sum() >= 2:
            out.append({"date": pd.Timestamp(d)
                        , "oni_1": float(rel.loc[m.tolist(), "oni"].iloc[-1]),
                        "oni_2": float(rel.loc[m.tolist(), "oni"].iloc[-2])})
        elif m.sum() == 1:
            out.append({"date": pd.Timestamp(d),
                        "oni_1": float(rel.loc[m.tolist(), "oni"].iloc[-1]),
                        "oni_2": np.nan})
        else:
            out.append({"date": pd.Timestamp(d), "oni_1": np.nan, "oni_2": np.nan})
    return pd.DataFrame(out)


def jjas_dates() -> list[date]:
    out = []
    for y in range(2015, 2025):
        for mth, last in ((6, 30), (7, 31), (8, 31), (9, 30)):
            for d in range(1, last + 1):
                out.append(date(y, mth, d))
    return out


if __name__ == "__main__":
    imd = imd_series()
    cells = select_pilot_cells(imd)
    print(f"domains cells after validity filter: {len(cells)}")
    print(cells.head(8).to_string(index=False))