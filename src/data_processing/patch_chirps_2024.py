"""Patch the 3 missing CHIRPS 2024 days (Jul 14/23/25) into the pilot NetCDF.

Uses the same COG windowed-read + coordinate conventions as download_chirps.py, but
with more retries and staggered backoff. Rebuilds the full calendar year and
re-records the checksum. Idempotent: if the file is already complete, exits 0.
"""
from __future__ import annotations

import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_pipeline_utils import record_checksum  # noqa: E402

MISSING = [date(2024, 7, 14), date(2024, 7, 23), date(2024, 7, 25)]
COGS = "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/cogs"
BBOX = {"north": 20.7, "south": 9.8, "west": 72.4, "east": 81.1}
MAX_TRIES = 20
BASE_PATH = Path(__file__).resolve().parents[2] / "data" / "raw" / "chirps"
DEST = BASE_PATH / "chirps_v3.0_rnl_2024_pilot.nc"


def read_one(day: date):
    import rasterio
    from rasterio.windows import from_bounds

    url = f"{COGS}/{day.year}/chirps-v3.0.rnl.{day.year:04d}.{day.month:02d}.{day.day:02d}.cog"
    for attempt in range(1, MAX_TRIES + 1):
        try:
            with rasterio.open(url) as ds:
                win = from_bounds(BBOX["west"], BBOX["south"], BBOX["east"], BBOX["north"],
                                  transform=ds.transform)
                a = ds.read(1, window=win)
            return np.maximum(np.nan_to_num(a, nan=-9999.0), 0.0)
        except Exception as e:  # noqa: BLE001
            if attempt == MAX_TRIES:
                print(f"[err] {day} last-msg={e}")
                return None
            time.sleep(min(2 * attempt, 20))
    return None


def main() -> int:
    import xarray as xr

    with xr.open_dataset(DEST) as ds:
        if int(ds.sizes["time"]) == 366:
            print("[skip] 2024 already complete")
            return 0
        nlat, nlon = int(ds.sizes["lat"]), int(ds.sizes["lon"])
        lats, lons = ds.lat.values, ds.lon.values
        attrs = dict(ds.attrs)
        attrs.pop("missing_days", None)
        existing_times = ds.time.values
        full = ds["precip"].values

    arrs = []
    for d in MISSING:
        print(f"fetching {d} ...")
        a = read_one(d)
        if a is None:
            print(f"ABORT: {d} still failing after {MAX_TRIES} tries;")
            return 1
        if a.shape != (nlat, nlon):
            print(f"ABORT: {d} grid mismatch {a.shape} != ({nlat}x{nlon})")
            return 1
        arrs.append(a)
        print(f"  ok {d} shape={a.shape}")

    merged = {np.datetime64(existing_times[i], "D"): full[i]
              for i in range(existing_times.size)}
    for k, d in enumerate(MISSING):
        merged[np.datetime64(d, "D")] = arrs[k]

    cal = [np.datetime64(datetime(2024, 1, 1) + timedelta(days=i), "D") for i in range(366)]
    grids = np.stack([merged[t] for t in cal], axis=0)
    print(f"built {grids.shape} with {len(merged)} unique days")

    da = xr.DataArray(
        grids, dims=["time", "lat", "lon"],
        coords={"time": cal, "lat": lats, "lon": lons},
        name="precip",
        attrs=attrs | {"missing_days": 0,
                       "patched": "2024-07-14,2024-07-23,2024-07-25"},
    )
    da.attrs["_FillValue"] = -9999.0
    da.to_netcdf(DEST)
    record_checksum("chirps", DEST, "COG range-read (pilot bbox; patched)")
    print(f"[ok] patched {DEST.name}: days={grids.shape[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())