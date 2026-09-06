"""Download CHIRPS v3 daily rainfall (FINAL, rnl/ERA5-downscaled) for the pilot bbox.

Dataset verified 2026-09-02: https://data.chc.ucsb.edu/products/CHIRPS/v3.0/
- v3.0 final back-processed from Jan 1981; daily products: rnl (ERA5, 1981+) & sat (IMERG, 2001+).
- Full-res 0.05 global daily .tif ~13 MB/day (47 GB/10yr) => replaced with COG range-reads.

Strategy (per "extract only the required spatial region"):
  read each day's Cloud-Optimized GeoTIFF with rasterio using a WINDOWED read over the
  pilot bbox (HTTP range requests, no full-file download), then persist per-year regional
  NetCDFs. 4-way thread pool with retries (verified ~5s/day serially; COG window 218x174).

Source pattern (VERIFIED):
  https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/cogs/{year}/chirps-v3.0.rnl.{y}.{m}.{d}.cog
"""
from __future__ import annotations

import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_pipeline_utils import RAW, log_download, record_checksum  # noqa: E402

OUT_DIR = RAW / "chirps"
COGS = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/cogs"

# Pilot extraction box (from config/project.yaml, small margin outward to land mask)
BBOX = {"north": 20.7, "south": 9.8, "west": 72.4, "east": 81.1}
YEARS = list(range(2015, 2025))
WORKERS = 4
RETRIES = 4


def _cog_url(y: int, m: int, d: int) -> str:
    return f"{COGS}/{y}/chirps-v3.0.rnl.{y:04d}.{m:02d}.{d:02d}.cog"


def read_one(day: date) -> tuple[str, np.ndarray | None]:
    """Read one day's COG window; on failure retry then return None."""
    import rasterio  # local import: heavy, only needed in workers
    from rasterio.windows import from_bounds

    url = _cog_url(day.year, day.month, day.day)
    for attempt in range(1, RETRIES + 1):
        try:
            with rasterio.open(url) as ds:
                win = from_bounds(BBOX["west"], BBOX["south"], BBOX["east"], BBOX["north"],
                                  transform=ds.transform)
                a = ds.read(1, window=win)
            return day.isoformat(), np.maximum(np.nan_to_num(a, nan=-9999.0), 0.0)
        except Exception as e:  # noqa: BLE001
            if attempt == RETRIES:
                print(f"[err] {url} final: {e}")
                return day.isoformat(), None
            time.sleep(2 * attempt)
    return day.isoformat(), None


def year_path(year: int) -> Path:
    return OUT_DIR / f"chirps_v3.0_rnl_{year}_pilot.nc"


def year_complete(year: int) -> bool:
    """True only when the NetCDF holds the full calendar year (no silent truncation)."""
    import calendar

    dest = year_path(year)
    if not (dest.exists() and dest.stat().st_size > 1_000_000):
        return False
    try:
        import xarray as xr

        n = int(xr.open_dataset(dest).sizes["time"])
        expected = 366 if calendar.isleap(year) else 365
        return n == expected
    except Exception:  # noqa: BLE001
        return False


def run_year(year: int) -> None:
    dest = year_path(year)
    if year_complete(year):
        print(f"[skip] {year} already built (complete)")
        return
    start, end = date(year, 1, 1), date(year, 12, 31)
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    results: dict[str, np.ndarray | None] = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(read_one, d) for d in days]
        for k, fut in enumerate(as_completed(futs)):
            iso, arr = fut.result()
            results[iso] = arr
            if (k + 1) % 200 == 0:
                print(f"   {year}: {k + 1}/{len(days)} days read")

    valid = [d.isoformat() for d in days if results[d.isoformat()] is not None]
    missing = [d.isoformat() for d in days if results[d.isoformat()] is None]
    if not valid:
        print(f"[warn] {year}: no valid days")
        return
    arrays = [results[d] for d in valid]

    import xarray as xr

    stack = np.stack(arrays, axis=0)
    # lat/lon linears for the sampled window (match CHIRPS grid center convention)
    nrows, ncols = stack.shape[1], stack.shape[2]
    lats = np.linspace(BBOX["north"] - 0.025, BBOX["south"] + 0.025, nrows)
    lons = np.linspace(BBOX["west"] + 0.025, BBOX["east"] - 0.025, ncols)
    da = xr.DataArray(
        stack, dims=["time", "lat", "lon"],
        coords={"time": [np.datetime64(v, "D") for v in valid], "lat": lats, "lon": lons},
        name="precip",
        attrs={
            "units": "mm",
            "long_name": "CHIRPS v3.0 daily precipitation (final, rnl/ERA5)",
            "grid": "0.05 deg", "pilot_bbox": str(BBOX),
            "cog_source": COGS,
        },
    )
    da.attrs["_FillValue"] = -9999.0
    da.attrs["missing_days"] = len(missing)
    da.to_netcdf(dest)
    record_checksum("chirps", dest, "COG range-read (pilot bbox)")
    print(f"[ok] {year}: {len(valid)}/{len(days)} days, shape={stack.shape}, "
          f"missing={len(missing)}, {dest.stat().st_size/1e6:.1f} MB")
    if missing:
        log_download("chirps", COGS, dest, True, note=f"missing_days={missing[:20]}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    only = [int(a) for a in sys.argv[1:]]
    years = only or YEARS
    for y in years:
        run_year(y)
    print("CHIRPS complete.")


if __name__ == "__main__":
    main()