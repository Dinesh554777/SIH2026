# DATASET_LIMITATIONS

Honest catalog of limitations of the datasets researched/downloaded for SIH26086
(hyperlocal = block/village scale). Limitations marked "OBSERVED" were confirmed from the
downloaded files; others are documented from the scientific literature.

## 1. IMD 0.25-deg daily rainfall (GROUND_TRUTH)
- **Resolution gap**: 0.25° ≈ 27.5 km ≈ 755 km² cell — a whole district is 1-4 cells. NOT block/village
  scale; onset/break labels per block will be inherited from the nearest cell (documented in TRAINING_DATA_DESIGN).
- **Interpolation smoothing**: grid is a gauge-interpolation (Pai 2014, thin-plate splines + PRISM-like
  elevation); sub-grid orographic rain (Western Ghats escarpment in Satara/Coimbatore) is smeared.
- **Missing-value marker**: -999 in files OBSERVED; 0.0% missing in our period (OBSERVED), but coasts/extremes
  can clip to 0 at gauge-voids (interpret 0 carefully - not all zeros are "no rain").
- **Extreme daily values**: 979 mm observed in 2022 (OBSERVED in DATA_QUALITY_REPORT) - plausible (extremely
  heavy day) but single-day extremes near stations dominate; winsorization vs. retention decision needed
  at modeling stage.

## 2. CHIRPS v3.0 (HIGH_RES / VALIDATION)
- **Satellite+station blend**: over-forecasts light rain (wet-day frequency bias), under-forecasts extremes.
- **rnl chain caveat**: "final" rnl uses ERA5 reanalysis forcing for 1981-2000; for our epoch 2015-2024 it is
  IMERG-era (`sat`) aligned, but the two variants differ — comparison figures should note which chain is used
  (we extracted `rnl`).
- **No INDIA local gauge calibration**: CHIRPS blend weights include GTS-reporting stations in India but not
  IMD's full network; independent from IMD grid (GOOD for cross-validation, but not identical in intent).
- **0.05° still not village scale**: ≈ 5.5 km vs block centroids; good for district/cluster, not village homes.
- **COG range-read**: we read only the pilot window; west/east lon wrap and ocean cells are NaN/sea — sea
  cells excluded downstream.

## 3. ERA5 (AUTH_REQUIRED - ATMOSPHERIC_PREDICTORS)
- **Credential gate**: not downloadable without CDS API key; licence acceptance in CDS UI required.
- **0.25° & hourly**: fine for synoptic predictors, but MSLP/T2M at 0.25° still masks local valley wind,
  orographic T inversion (Ghats).
- **Precipitation within ERA5** is model-scheme-generated (not gauge-merged like IMD) — we will NOT use ERA5
  precip as truth; only as predictor context.

## 4. NOAA ONI (CLIMATE_PREDICTOR)
- **3-month running mean**: gives only seasonal ENSO phase — no intra-seasonal/sub-seasonal signal.
- **Calendar overlap**: a DJF ONI value overlaps adjacent NDJ/JFM; feature window must lag target by >=1
  season (see DATA_LEAKAGE_REPORT).
- **Index, not grid**: single value per month for whole India; no spatial discrimination between Pune and
  Coimbatore (both see same ENSO forcing — but their local response differs; that local response is learned
  from local predictors).

## 5. NASA POWER (SUPPLEMENTARY / VALIDATION)
- **Coarse & reanalysis-derived**: 0.5° lat × 0.625° lon (MERRA-2 native — OBSERVED in files: LON step
  0.625), ~55 km — coarsest dataset in the stack.
- **PRECTOTCORR is model-adjusted precip**, not gauge truth; use only for cross-checking with IMD, never as label.
- **-999 fill**: missing source/outside-range encoded -999 (OBSERVED, declared in header); must be masked.
- **LST vs UTC**: POWER daily files are in Local Solar Time by default (OBSERVED: "in LST" header). ERA5 is
  UTC. A daily-mean mismatch of 0-1 h is harmless for daily means, but hourly features would need alignment.

## Cross-cutting
- **Block/village scale is NOT achievable with any of these grids alone**; combined with block centroids the
  system inherits the closest-cell value. This is a stated limitation of the problem's "hyperlocal" ambition —
  mitigation: per-block calibration on IMD-vs-village checklists if provided by MoES, or treat outputs as
  block-cluster probabilistic guidance with calibrated intervals.
- **Period 2015-2024** is fixed; 2024 retained as TEST. Interannual variability (El Niño 2015-16, La Niña
  2020-22) is represented in TRAIN, but a 10-year record is short for extreme-tail skill claims.
- All statuses/roles captured in data/metadata/*.json; anything UNVERIFIED stays unverified (no fabrication).