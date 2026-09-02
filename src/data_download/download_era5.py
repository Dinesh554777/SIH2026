"""ERA5 download scaffold (CDS API, AUTH-REQUIRED).

Verified 2026-09-02:
- Dataset: ERA5 hourly data on single levels from 1940 to present
  https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels
- Regridded to 0.25x0.25; 1940-present; ECMWF/C3S Copernicus.
AUTH REQUIREMENT (documented, never bypassed):
  1) Free ECMWF/Copernicus account
  2) Accept the dataset licence in the CDS web UI
  3) Create ~/.cdsapirc or set CDSAPI_URL/CDSAPI_KEY from https://cds.climate.copernicus.eu/profile
No credentials present in this repo. This script refuses to run without them.

Target variables (single-level, hourly, aggregated to daily):
  tp  (total precipitation), t2m (2m temperature), d2m (2m dewpoint),
  sp  (surface pressure), msl (mean sea level pressure),
  u10, v10 (10m wind components)
Extraction: pilot bbox {'north':20.7,'south':9.8,'west':72.4,'east':81.1}, years 2015-2024.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_pipeline_utils import RAW, log_download  # noqa: E402

OUT_DIR = RAW / "era5"
BBOX = {"north": 20.7, "south": 9.8, "west": 72.4, "east": 81.1}
VARIABLES = ["total_precipitation", "2m_temperature", "2m_dewpoint_temperature",
             "surface_pressure", "mean_sea_level_pressure", "10m_u_component_of_wind",
             "10m_v_component_of_wind"]
YEARS = list(range(2015, 2025))


def _has_credentials() -> bool:
    cfg = Path.home() / ".cdsapirc"
    return cfg.exists() or (os.environ.get("CDSAPI_URL") and os.environ.get("CDSAPI_KEY"))


def build_request(year: int) -> dict:
    return {
        "product_type": "reanalysis",
        "variable": VARIABLES,
        "data_format": "netcdf",
        "download_format": "unarchived",
        "year": str(year),
        "month": [f"{m:02d}" for m in range(1, 13)],
        "day": [f"{d:02d}" for d in range(1, 32)],
        "time": ["00:00", "06:00", "12:00", "18:00"],
        "area": [BBOX["north"], BBOX["west"], BBOX["south"], BBOX["east"]],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not _has_credentials():
        print("ERA5 acquisition BLOCKED: CDS API credentials required.")
        print("Configure ~/.cdsapirc (url + key) from https://cds.climate.copernicus.eu/profile")
        print("and accept dataset licence in the CDS web UI. No bypass implemented.")
        for y in YEARS:
            log_download("era5", "cds-api", Path("n/a"), False,
                         note="AUTH_REQUIRED: CDS API key not configured")
        return
    import cdsapi  # noqa: PLC0415

    client = cdsapi.Client()
    for y in YEARS:
        dest = OUT_DIR / f"era5_single_levels_{y}_pilot.nc"
        client.retrieve("reanalysis-era5-single-levels", build_request(y), str(dest))
        log_download("era5", "cds-api", dest, True, note="hourly->daily aggregation TBD")
    print("ERA5 download started. Hourly fields require daily aggregation post-process.")


if __name__ == "__main__":
    main()