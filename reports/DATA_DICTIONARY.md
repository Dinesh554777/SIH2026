# DATA_DICTIONARY (data-research phase)

Every artifact actually produced in this research work, with unit/missing conventions.
Raw files are never modified; all derived products keep provenance in data/metadata/*.json.

## IMD (GROUND_TRUTH) — data/raw/imd/ind<year>_rfp25.nc (2015-2024)
- NetCDF-4 CLASSIC; variable `RAINFALL(TIME,LATITUDE,LONGITUDE)` float32, mm/day.
- dims: TIME (365/366/day), LATITUDE (129, 6.5-38.5N step 0.25), LONGITUDE (135, 66.5-100.0E step 0.25).
- TIME units: "days since 1900-12-31 00:00:00", calendar GREGORIAN.
- missing: -999.0 (both `missing_value` and `_FillValue`). Observed 0% missing in our period.
- Example observed extreme max: 979.1 mm (2022).

## CHIRPS (VALIDATION/HIGH-RES) — data/raw/chirps/chirps_v3.0_rnl_<year>_pilot.nc (2015-2024)
- NetCDF written by extraction: variable `precip(time,lat,lon)` float32.
- time: daily ISO; lat: 9.8-20.7N step 0.05 (218 points); lon: 72.4-81.1E step 0.05 (174 points)
  (grid centers offset by +0.025 in the writer — documented discrepancy to resolve in regrid step).
- units mm; missing/_FillValue: -9999.0 (set for ocean/void cells; NOT actual precip).
- Source COG: `https://data.chc.ucsb.edu/products/CHIRPS/v3.0/daily/final/rnl/cogs/<year>/chirps-v3.0.rnl.<y>.<m>.<d>.cog`

## ERA5 (ATM PREDICTORS) — data/raw/era5/ (AUTH_REQUIRED, not yet present)
- Target: reanalysis-era5-single-levels; variables tp,t2m,d2m,sp,msl,u10,v10; hourly; 0.25°.
- Not downloaded this session (needs CDS API key). Metadata JSON = AUTH_REQUIRED.

## NOAA ONI (CLIMATE_PREDICTOR) — data/raw/noaa/
- `oni.ascii.txt`: columns SEAS(3-letter), YR(4-digit), TOTAL(SST C), ANOM(delta C); 3-month running mean;
  918 rows 1950-2026; 120 rows in 2015-2024. No missing rows.
- `oni_v6_page.html`: provenance snapshot of the ONI v6 page (html).

## NASA POWER (SUPPLEMENTARY/VALIDATION) — data/raw/nasa/nasa_power_daily_<PARAM>_b<BAND>_<YEAR>.csv
- Header block (lines starting with `#` within `-BEGIN HEADER-`/`-END HEADER-`), then CSV rows:
  `LAT,LON,YEAR,DOY,<PARAM>` (also a trailing `...meteorologicalUse`/misc column in some year files —
  unify on first 5 cols).
- Units from header per param: T2M/T2MDEW/T2M_MAX/T2M_MIN (C), RH2M (%), PRECTOTCORR (mm/day),
  PS (hPa), WS10M/WS10M_MAX (m/s). Grid: 0.5° lat x 0.625° lon (MERRA-2 native, OBSERVED).
- Missing/outside-range: -999.
- Bands: b1 lat 10.0-20.0, b2 lat 20.0-22.0; lon 72.6-80.9E. 180 files (9 params x 2 bands x 10 years).

## Derived/validated artifacts
- data/metadata/<dataset>.json (status/role/URLs)
- data/checksums.csv (sha256 + timestamp + source_url per file)
- reports/DATA_QUALITY_REPORT.md, COVERAGE_REPORT.md, DATA_DOWNLOAD_LOG.md,
  RAINFALL_DATASET_COMPARISON.md (pending CHIRPS), DATA_SOURCES.md, DATASET_RECOMMENDATION.md,
  TRAINING_DATA_DESIGN.md, DATA_LEAKAGE_REPORT.md, DATASET_LIMITATIONS.md
- config/project.yaml holds geo/split/period decisions (single source of truth for extraction).