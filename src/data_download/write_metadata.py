"""Emit data/metadata/<dataset>.json for all five research datasets.

Values come ONLY from web-verification performed 2026-09-02 + what the
downloaded files actually contain. Anything not confirmed stays UNVERIFIED.
Statuses:
  VERIFIED      : source reachable + data obtained this session
  AUTH_REQUIRED : source is official but download requires credentials (ERA5)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_pipeline_utils import write_metadata  # noqa: E402

REQUIRED_PERIOD = {"start": "2015-01-01", "end": "2024-12-31"}


def main() -> None:
    write_metadata("imd", {
        "dataset_name": "IMD gridded rainfall (0.25x0.25 deg daily)",
        "provider": "India Meteorological Department (IMD Pune)",
        "official_url": "https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html",
        "api_url": "https://www.imdpune.gov.in/cmpg/Griddata/RF25.php",
        "license": "IMD research dissemination (free for research; cite Pai et al. 2014)",
        "version": "0.25-deg daily (Pai et al., 2014, MAUSAM)",
        "temporal_coverage": "1901-01-01 .. 2024-12-31 (present)",  # as-indicated by source, verified 2026-09-02
        "spatial_resolution": "0.25 x 0.25 deg (135 lon x 129 lat)",
        "temporal_resolution": "daily (mm/day)",
        "variables": ["RAINFALL (mm/day, -999 missing)"],
        "geographic_coverage": "India mainland 66.5E-100E, 6.5N-38.5N",
        "access_method": "HTTP POST RF25.php {RF25=<year>} -> yearly netCDF (verified)",
        "download_timestamp": "2026-09-02T00:00:00Z",
        "checksum": "see data/checksums.csv (per-year sha256)",
        "citation": "Pai et al. (2014) MAUSAM 65(1):1-18",
        "role": "GROUND_TRUTH",
        "suitability": "Primary reference rainfall for station/grid verification and thumb-label onset/break targets",
        "limitations": "225 km2 grid cell - represents district/cluster, not a village point; gauge-interpolation smoothing",
        "status": "VERIFIED",
    })
    write_metadata("chirps", {
        "dataset_name": "CHIRPS v3.0 daily precipitation (FINAL)",
        "provider": "UCSB Climate Hazards Center",
        "official_url": "https://www.chc.ucsb.edu/data/chirps",
        "api_url": "https://data.chc.ucsb.edu/products/CHIRPS/v3.0/",
        "license": "CC-BY-4.0 / doi:10.15780/G2JQ0P",
        "version": "v3.0 (final, rnl/ERA5-downscaled daily)",
        "temporal_coverage": "1981-01-01 .. present",
        "spatial_resolution": "0.05 x 0.05 deg (coarsened p25 = 0.25)",
        "temporal_resolution": "daily (mm/day)",
        "variables": ["precip (mm/day)"],
        "geographic_coverage": "Global 50S-50N (pilot bbox extracted only)",
        "access_method": "COG range-read window over pilot bbox (verified)",
        "download_timestamp": "2026-09-02T00:00:00Z",
        "checksum": "see data/checksums.csv (per-year pilot netcdf)",
        "citation": "Funk et al. (2015) Scientific Data 2:150066",
        "role": "HIGH_RESOLUTION_RAINFALL / VALIDATION",
        "suitability": "0.05-deg finer than IMD; used for cross-validation and spatial downscaling at block scale",
        "limitations": "Satellite+station blend; overestimates light rain, rare extremes; INDIA 2015-on final uses rnl chain; not gauge-truth-verified locally",
        "status": "VERIFIED",
    })
    write_metadata("era5", {
        "dataset_name": "ERA5 hourly on single levels",
        "provider": "ECMWF / Copernicus Climate Data Store",
        "official_url": "https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels",
        "api_url": "cds.climate.copernicus.eu (CDS API)",
        "license": "Copernicus licence terms (free, must accept licence in CDS UI)",
        "version": "ERA5 (ECMWF reanalysis), 0.25 deg",
        "temporal_coverage": "1940-01-01 .. present",
        "spatial_resolution": "0.25 x 0.25 deg",
        "temporal_resolution": "hourly (aggregate to daily for features)",
        "variables": ["total_precipitation, 2m_temperature, 2m_dewpoint_temperature, surface_pressure, mean_sea_level_pressure, 10m_u/v_wind"],
        "geographic_coverage": "Global (pilot bbox extraction planned)",
        "access_method": "CDS API REQUIRES free account + licence acceptance + ~/.cdsapirc key",
        "download_timestamp": "UNVERIFIED",
        "checksum": "UNVERIFIED",
        "citation": "Hersbach et al. (2020) QJRMS 146:1999-2049",
        "role": "ATMOSPHERIC_PREDICTORS",
        "suitability": "Main predictor source for onset/break detection (moisture, wind, MSLP patterns)",
        "limitations": "AUTH_REQUIRED - not downloaded this session; hourly->daily aggregation step needed; 0.25-deg not block-scale",
        "status": "AUTH_REQUIRED",
    })
    write_metadata("noaa", {
        "dataset_name": "NOAA CPC Oceanic Nino Index (ONI) v6",
        "provider": "NOAA NWS CPC",
        "official_url": "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/",
        "api_url": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
        "license": "US Government public domain (NWS)",
        "version": "ONI v6 (ERSSTv5/v6, Nino 3.4 3-month mean SST anomaly)",
        "temporal_coverage": "1950-01 .. 2026-05 (download verified; file covers 1950-2026)",
        "spatial_resolution": "Nino 3.4 region (5N-5S, 120-170W) index - no grid",
        "temporal_resolution": "3-month running (JJAS etc.)",
        "variables": ["ONI SST anomaly (deg C)"],
        "geographic_coverage": "Equatorial Pacific Nino 3.4",
        "access_method": "HTTP GET text file (verified)",
        "download_timestamp": "2026-09-02T00:00:00Z",
        "checksum": "see data/checksums.csv",
        "citation": "NOAA CPC ONI (ERSSTv5/v6)",
        "role": "CLIMATE_PREDICTOR",
        "suitability": "ENSO-phase context feature (correlated with ISM interannual variability)",
        "limitations": "Monthly/3-month index; only seasonal-timescale driver, not daily-local physics",
        "status": "VERIFIED",
    })
    write_metadata("nasa", {
        "dataset_name": "NASA POWER daily meteorology (MERRA-2)",
        "provider": "NASA Langley POWER Project",
        "official_url": "https://power.larc.nasa.gov/docs/",
        "api_url": "https://power.larc.nasa.gov/api/temporal/daily/",
        "license": "NASA open data (no restrictions for research use)",
        "version": "POWER API v2.x (MERRA-2 reanalysis, AG community v837)",
        "temporal_coverage": "1981-01-01 .. near-real-time",
        "spatial_resolution": "0.5 x 0.5 deg",
        "temporal_resolution": "daily",
        "variables": ["T2M, T2MDEW, T2M_MAX, T2M_MIN, PRECTOTCORR, PS, RH2M, WS10M, WS10M_MAX"],
        "geographic_coverage": "Global (pilot bbox 9.9-20.6N, 72.6-80.9E downloaded)",
        "access_method": "REST regional daily endpoint, no auth (verified)",
        "download_timestamp": "2026-09-02T00:00:00Z",
        "checksum": "see data/checksums.csv",
        "citation": "NASA POWER docs: https://power.larc.nasa.gov/docs/services/api/",
        "role": "SUPPLEMENTARY / VALIDATION",
        "suitability": "Cross-check T2M/RH/PS against ERA5 predictors; independent daily field",
        "limitations": "0.5-deg coarse; PRECTOTCORR is adjusted MERRA-2 precip, NOT rain-gauge verified; LST vs UTC time-standard nuance",
        "status": "VERIFIED",
    })

    # Dataset-registry snapshot appended to a reusable JSON for later steps
    print("metadata files written:")
    for p in sorted((Path(__file__).resolve().parents[1] / "data" / "metadata").glob("*.json")):
        print(f"  {p.name}")


if __name__ == "__main__":
    main()