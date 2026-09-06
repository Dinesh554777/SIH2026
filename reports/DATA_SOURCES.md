# DATA_SOURCES

Purpose: registry of the authoritative data sources researched, verified, and (where free) downloaded
for the SIH26086 hyperlocal monsoon onset/break system. Nothing in this document is fabricated:
every entry was either confirmed by direct request (date: 2026-09-02) or marked UNVERIFIED / AUTH_REQUIRED.

Required period: **2015-01-01 .. 2024-12-31** (daily). Pilot bbox: lat 9.8–20.7N, lon 72.4–81.1E
(Tamil Nadu, Maharashtra, Karnataka districts).

---

## 1. IMD gridded daily rainfall 0.25 deg — GROUND_TRUTH

- Provider: India Meteorological Department (IMD), Pune — National Data Centre.
- Reference: Pai et al. (2014), "Development of a new high spatial resolution (0.25°×0.25°) Long Period (1901–2010) daily gridded rainfall data set over India and its comparison with existing data sets over the region", MAUSAM 65(1), 1–18.
- Coverage: 1901–2024 (present), continuous; grid 135 (lon 66.5–100.0E) × 129 (lat 6.5–38.5N).
- Resolution: 0.25°×0.25°, daily, mm.
- Variables: RAINFALL (mm/day; missing = -999.0).
- Files: yearly NetCDF-4 `ind<year>_rfp25.nc` (~25.5 MB each for recent years).
- Access (VERIFIED 2026-09-02): HTTP POST to `https://www.imdpune.gov.in/cmpg/Griddata/RF25.php`
  with form field `RF25=<year>`; server returns attachment `ind<year>_rfp25.nc`. Source page:
  `https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html`.
- Roll in using daily ingested yields ~62k grid-days for our period download was done directly (10 years,
  2015–2024) — see data/raw/imd.
- QC so far (see DATA_QUALITY_REPORT): 0.0% missing, 68–75% zero days, max daily up to 979 mm (extreme event,
  2022), annual mean ~2.7–3.5 mm/day across India.
- Status: **VERIFIED + DOWNLOADED (2015–2024)**.

## 2. CHIRPS v3.0 daily precipitation — HIGH-RES / VALIDATION

- Provider: Climate Hazards Center (UCSB).
- Reference: Funk et al. (2015), Scientific Data 2:150066. doi:10.15780/G2JQ0P. License CC-BY-4.0.
- Coverage: global 50S–50N, back-processed FINAL from 1981-01-01 to present.
- Resolution: 0.05°×0.05° daily (mm). Pulse daily versions `chirps-v3.0.<variant>.YYYY.MM.DD.tif`.
- Variants (VERIFIED 2026-09-02):
  - `daily/final/rnl/...` — downscaled to ERA5 interim-backfill; available from 1981.
  - `daily/final/sat/...` — IMERG-era blend; from 2001.
  - `daily/final/rnl/p25/...` — 0.25°-grid daily tifs (~630–670 KiB/day).
  - `daily/final/rnl/cogs/...` — Cloud-Optimized GeoTIFFs (~18 MiB/day) for windowed range-reads.
  - `daily/final/rnl/netcdf/byYear|byMonth|...` — packaged netCDF.
- Full-res download for the 10-year period ≈ 47 GB — NOT adopted; instead COG windowed reads over the
  pilot bbox only (~218×174 cells/day) were used to write `chirps_v3.0_rnl_<year>_pilot.nc`.
- Status: **VERIFIED + EXTRACTED (pilot bbox, 2015-2024)**. 3653/3653 days complete (100%);
  truncated 2019-2021 files rebuilt after interrupted runs; 2024 (Jul 14, 23, 25) patched in later.
  Coverage = FULL_COVERAGE. Each year is 0.05°×0.05° over lat 9.8-20.7N, lon 72.4-81.1E, ~55 MB.
  Checksums in data/checksums.csv.

## 3. ERA5 (Copernicus CDS) hourly single levels — ATMOSPHERIC_PREDICTORS

- Provider: ECMWF, Copernicus Climate Data Store.
- Reference: Hersbach et al. (2020), QJRMS 146(730):1999–2049.
- Coverage: 1940–01-01 to present; 0.25°×0.25° hourly.
- Variables wanted: 2m temperature, 2m dewpoint, surface pressure, mean sea level pressure,
  10m u/v wind, total precipitation.
- Access: CDS API only (Python `cdsapi`), REQUIRES free account, licence acceptance in CDS UI, and
  API key (`~/.cdsapirc`). **AUTH_REQUIRED** — documented, not downloaded this session (never bypassed).
- Status: **VERIFIED SOURCE / NOT DOWNLOADED (credentials needed)**. Download scaffold ready in
  src/data_download/download_era5.py.

## 4. NOAA CPC ONI (Oceanic Niño Index) v6 — CLIMATE_PREDICTOR

- Provider: NOAA NWS Climate Prediction Center.
- Reference: `https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/`.
- Product: Niño 3.4 (5N–5S, 120–170W) 3-month running mean SST anomaly, ERSSTv5/v6; 1950–present.
- Resolution: seasonal (3-month mean) index — no grid.
- Access (VERIFIED 2026-09-02): `https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt`.
- Download: data/raw/noaa/oni.ascii.txt (23894 B) — 918 rows 1950–2026; 120 rows within 2015–2024
  (12 seasons × 10 years), no gaps.
- Status: **VERIFIED + DOWNLOADED**.
- Note: NOAA operational index is now `RONI`; ONI retained as the established reference.

## 5. NASA POWER (MERRA-2) daily meteorology — SUPPLEMENTARY / VALIDATION

- Provider: NASA Langley Atmospheric Science Data Center (POWER project).
- Docs: `https://power.larc.nasa.gov/docs/services/api/temporal/daily/`.
- Coverage: 1981-01-01 .. near-real-time; 0.5°×0.5° daily.
- Variables (AG community, VERIFIED param names): T2M, T2MDEW, T2M_MAX, T2M_MIN, PRECTOTCORR,
  PS, RH2M, WS10M, WS10M_MAX.
- Access (VERIFIED 2026-09-02): REST `.../api/temporal/daily/regional` — max 1 parameter/request,
  latitude range 2–10°; returns CSV. No auth.
- Download: data/raw/nasa/nasa_power_daily_<PARAM>_b<BAND>_<YEAR>.csv
  (2 bands × 10 years × 9 params, 180 files; ~2.5 MB each).
- Status: **VERIFIED + DOWNLOADED (2015–2024)**.

---

## Summary of roles
| Dataset | Role | Downloaded? | Notes |
| --- | --- | --- | --- |
| IMD 0.25 daily | GROUND_TRUTH | yes (2015–2024) | primary onset/break label reference |
| CHIRPS v3.0 0.05 | HIGH_RES + VALIDATION | in progress (pilot bbox) | independent high-res comparison |
| ERA5 hourly | ATMOSPHERIC_PREDICTORS | no (AUTH_REQUIRED) | feature provider; needs CDS key |
| NOAA ONI | CLIMATE_PREDICTOR | yes | seasonal ENSO context |
| NASA POWER | SUPPLEMENTARY/VALIDATION | yes | T2M/RH/PS cross-check at 0.5° |