"""Rainfall dataset comparison: IMD 0.25 vs CHIRPS (0.05 pilot bbox, regridded to IMD grid).

All metrics computed from actual downloaded files (no fabricated values).
Comparison is on the pilot bbox. IMD daily is coarse (0.25); CHIRPS pilot is 0.05.
Purposes:
  - whether CHIRPS can serve as high-resolution validation / downscaling source
  - quantify bias (esp. light-rain overestimation) vs IMD ground truth
Outputs:
  reports/RAINFALL_DATASET_COMPARISON.md (tables)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_pipeline_utils import REPORTS, DATA  # noqa: E402

BBOX = {"north": 20.7, "south": 9.8, "west": 72.4, "east": 81.1}
YEARS = list(range(2015, 2025))


def imd_pilot() -> dict:
    """Return IMD daily over BBOX subset as {dates, data (days,lat,lon), lats, lons}."""
    import netCDF4 as nc
    from cftime import num2date

    lat0, lon0 = None, None
    dates: list[str] = []
    blocks = []
    for year in YEARS:
        ds = nc.Dataset(DATA / "raw" / "imd" / f"ind{year}_rfp25.nc")
        lat = ds.variables["LATITUDE"][:].astype(float)
        lon = ds.variables["LONGITUDE"][:].astype(float)
        rain = ds.variables["RAINFALL"][:]
        # netCDF4 returns masked arrays; _FillValue positions are already masked.
        # .filled(np.nan) converts masked -> NaN in float, preserving 0.0 as valid.
        rain = np.ma.filled(rain, np.nan).astype(float)
        li = np.argwhere((lat >= BBOX["south"] - 0.4) & (lat <= BBOX["north"] + 0.4)).ravel()
        lo = np.argwhere((lon >= BBOX["west"] - 0.4) & (lon <= BBOX["east"] + 0.4)).ravel()
        if lat0 is None:
            lat0, lon0 = lat[li], lon[lo]
        blocks.append(rain[:, li[:, None], lo[None, :]])
        tt = num2date(ds.variables["TIME"][:], ds.variables["TIME"].units,
                      calendar=getattr(ds.variables["TIME"], "calendar", "standard"))
        dates += [str(x)[:10] for x in tt]
        ds.close()
    return {"dates": dates, "data": np.concatenate(blocks, axis=0), "lats": lat0, "lons": lon0}


def lighten(combo: dict) -> dict:
    return {"dates": combo["dates"], "data": combo["data"], "lats": combo["lats"], "lons": combo["lons"]}


def chirps_to_imd():
    """Build CHIRPS regridded onto the IMD bbox grid (nearest-neighbour 0.05->0.25).

    CHIRPS netCDFs store lat descending (north-up, rasterio convention); xarray
    requires monotonic-increasing for .sel/.interp, so we flip to ascending and
    mask fill (-9999) to NaN.
    """
    import xarray as xr

    chirp_files = sorted((DATA / "raw" / "chirps").glob("chirps_v3.0_rnl_*_pilot.nc"))
    if not chirp_files:
        return None
    parts = [xr.open_dataset(p)["precip"] for p in chirp_files]
    # align on lat/lon then concat on time; each file shares the same lat/lon grid
    ds = xr.concat(parts, dim="time")
    del parts
    ds = ds.where(ds != -9999.0, np.nan)
    if float(ds.lat[1] - ds.lat[0]) < 0:  # descending -> flip ascending
        ds = ds.isel(lat=slice(None, None, -1))
    imd = imd_pilot()
    # restrict IMD sampling grid to the CHIRPS-covered range (no edge extrapolation)
    lat_keep = (imd["lats"] >= float(ds.lat.min())) & (imd["lats"] <= float(ds.lat.max()))
    lon_keep = (imd["lons"] >= float(ds.lon.min())) & (imd["lons"] <= float(ds.lon.max()))
    lat = imd["lats"][lat_keep]
    lon = imd["lons"][lon_keep]
    regridded = ds.sel(lon=lon, lat=lat, method="nearest")
    # subset raw IMD array to the same index space (order = imd lats/lons)
    imd["data"] = imd["data"][:, lat_keep, :][:, :, lon_keep]
    imd["lats"], imd["lons"] = lat, lon
    return regridded, imd, chirp_files


def compare(a_day: np.ndarray, b_day: np.ndarray) -> dict:
    mask = np.isfinite(a_day) & np.isfinite(b_day)
    if mask.sum() == 0:
        return {k: np.nan for k in
                ("corr", "mae", "rmse", "bias", "wet_a%", "wet_b%",
                 "p95_a", "p95_b", "p99_a", "p99_b", "jjas_a", "jjas_b")}
    av, bv = a_day[mask], b_day[mask]
    corr = float(np.corrcoef(av, bv)[0, 1]) if (np.std(av) > 0 and np.std(bv) > 0) else np.nan
    return {
        "corr": corr,
        "mae": float(np.mean(np.abs(bv - av))),
        "rmse": float(np.sqrt(np.mean((bv - av) ** 2))),
        "bias": float(np.mean(bv - av)),
        "wet_a%": round(float(np.mean(av >= 1) * 100), 2),
        "wet_b%": round(float(np.mean(bv >= 1) * 100), 2),
        "p95_a": float(np.nanpercentile(av, 95)),
        "p95_b": float(np.nanpercentile(bv, 95)),
        "p99_a": float(np.nanpercentile(av, 99)),
        "p99_b": float(np.nanpercentile(bv, 99)),
    }


def main() -> None:
    regridded, imd, chirp_files = chirps_to_imd()
    if regridded is None:
        print("CHIRPS files not ready; re-run after CHIRPS download completes.")
        return
    chirps = regridded.values[:, :, :]  # (days_sub, lat, lon)

    # align by date
    a_dates = np.array(imd["dates"], dtype="datetime64[D]")
    b_dates = np.array([str(x)[:10] for x in regridded.time.values], dtype="datetime64[D]")

    rows = []
    for year in YEARS:
        m = (a_dates >= np.datetime64(f"{year}-01-01")) & (a_dates <= np.datetime64(f"{year}-12-31"))
        ai = np.argwhere(m).ravel()
        if len(ai) == 0:
            continue
        m2 = (b_dates >= a_dates[ai[0]]) & (b_dates <= a_dates[ai[-1]])
        bi = np.argwhere(m2).ravel()
        n = min(len(ai), len(bi))
        if n == 0:  # year not yet extracted in CHIRPS
            continue
        a_block = imd["data"][ai[:n]]
        b_block = chirps[bi[:n]]
        r = compare(a_block.reshape(-1), b_block.reshape(-1))
        r.update({"days": n})
        # monsoon (JJAS) seasonal totals, grid-mean of daily mean * days-in-season
        jj = np.datetime64(f"{year}-06-01") <= a_dates[ai[:n]]
        jj &= a_dates[ai[:n]] <= np.datetime64(f"{year}-09-30")
        jj_idx = np.argwhere(jj).ravel()
        if len(jj_idx) > 0:
            r["jjas_a"] = float(np.nanmean(imd["data"][ai[jj_idx]]))
            r["jjas_b"] = float(np.nanmean(chirps[bi[jj_idx]]))
        rows.append({"year": year, **r})
    # whole-period
    n = min(len(a_dates), len(b_dates))
    r0 = compare(imd["data"][:n].reshape(-1), chirps[:n].reshape(-1))
    r0.update({"days": n})
    rows.append({"year": "2015-2024 (available)", **r0})

    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = [
        "# RAINFALL_DATASET_COMPARISON (IMD 0.25 vs CHIRPS v3.0 0.05 -> IMD grid)\n",
        "Metrics over pilot bbox (lat 9.8-20.7N, lon 72.4-81.1E). Wet-day = >=1 mm. "
        "A=IMD, B=CHIRPS. bias = mean(B-A). Days = CHIRPS days matched that year.\n",
        "NOTE: rows/progress limited to years where CHIRPS pilot extraction has completed.\n",
        "| period | days | corr | MAE | RMSE | bias | wet A% | wet B% | p95 A | p95 B | p99 A | p99 B | JJAS A | JJAS B |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        if "jjas_a" in r:
            lines.append(
                f"| {r['year']} | {r['days']} | {r['corr']:.3f} | {r['mae']:.2f} | {r['rmse']:.2f} | "
                f"{r['bias']:+.3f} | {r['wet_a%']} | {r['wet_b%']} | {r['p95_a']:.1f} | {r['p95_b']:.1f} | "
                f"{r['p99_a']:.1f} | {r['p99_b']:.1f} | {r['jjas_a']:.2f} | {r['jjas_b']:.2f} |")
        else:
            lines.append(
                f"| {r['year']} | {r['days']} | {r['corr']:.3f} | {r['mae']:.2f} | {r['rmse']:.2f} | "
                f"{r['bias']:+.3f} | {r['wet_a%']} | {r['wet_b%']} | {r['p95_a']:.1f} | {r['p95_b']:.1f} | "
                f"{r['p99_a']:.1f} | {r['p99_b']:.1f} | - | - |")
    REPORT = REPORTS / "RAINFALL_DATASET_COMPARISON.md"
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"comparison report -> {REPORT}")
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()