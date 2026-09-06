# DATASET_RECOMMENDATION

Decision on which datasets to use as GROUND_TRUTH, PREDICTORS and VALIDATION for the
SIH26086 hyperlocal monsoon onset/break system. Based strictly on verified facts from
2026-09-02 research + downloaded data + DATA_QUALITY_REPORT + RAINFALL_DATASET_COMPARISON.

## Scoring method (11 criteria, each 1-5; totals compared within role)

Criteria: (1) availability/access ease, (2) license/business suitability, (3) spatial resolution,
(4) temporal resolution, (5) coverage of required period, (6) data quality (missing%), (7) documentation,
(8) scientific validation/literature, (9) independence (for validation role), (10) volume/storage footprint,
(11) latency to block-scale hyperlocal usefulness.

## 1. Rainfall (ground-truth decision)

| Dataset | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | Total | Role |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| IMD 0.25 daily | 5 | 4 | 3 | 5 | 5 | 5 (0% missing) | 4 | 5 (Pai 2014) | 5 | 4 | 3 | - | GROUND_TRUTH |
| CHIRPS v3.0 0.05 | 4 | 5 (CC-BY-4.0) | 4 | 5 | 5 | 4 (see quality report) | 5 | 5 (Funk 2015) | 5 | 2 (COG reads needed) | 4 | - | VALIDATION/HIGH-RES |

IMD is the **recommended rainfall ground truth** for label generation: national data service, 0% missing in
our files, 0.25° daily for the whole period, free-for-research. CHIRPS v3.0 is recommended as the
**independent high-resolution validation layer** at 0.05° (rating 9 = 5 because it is a separate
institution/network from IMD). The quantitative cross-check table is reproduced from
RAINFALL_DATASET_COMPARISON.md (added after that report completes).

### Rainfall comparison verdict
- Full table lives in RAINFALL_DATASET_COMPARISON.md (10-year period, 3653 matched days, pilot bbox).
- **Full 2015-2024 results (IMD vs CHIRPS, CHIRPS regridded to IMD grid):**
  - Pixel-day correlation: **0.521**
  - MAE **3.99 mm**, RMSE **11.5 mm**, bias **+0.26 mm** (CHIRPS slightly wetter)
  - CHIRPS wet-day frequency **32.3%** vs IMD **23.6%** -> CHIRPS over-counts light-rain days
    (classic drizzle bias in satellite/ERA5-downscaled blends), consistently across years.
  - Per-year corr: 0.47-0.59 (2015-2024), weakest in 2021 (0.47) and 2015/2020 (0.48);
    strongest in 2019 (0.59) and 2023 (0.56); 2024 = 0.53 after patch.
  - Monsoon (JJAS) CHIRPS mean systematically BELOW IMD (typically 1-1.5 mm/day lower).
- **Verdict**: IMD remains GROUND_TRUTH for labels. CHIRPS is a CONFIRMED valid *independent*
  high-res validation/downscaling layer (r~0.52, low bias) but its drizzle over-counting means any
  CHIRPS-based label needs a wet-threshold correction. Use IMD for labels; use CHIRPS for spatial
  detail + independent cross-check; do NOT blend the two in one label stream.
- **Data completeness**: all datasets now FULL_COVERAGE (imd 3653, chirps 3653, nasa, noaa); the
  previously missing CHIRPS 2024 days (Jul 14, 23, 25) were fetched and patched in on a later
  attempt (server-side error), and truncated 2019-2021 files were rebuilt.

## 2. Predictors (multi-source)

| Dataset | Score (1-11 avg) | Role | Recommended? |
| --- | --- | --- | --- |
| ERA5 | avg ~4.5 (auth gate lowers 1) | ATM predictors (t2m/d2m/mslp/sp/u10/v10) | YES once CDS key available (AUTH_REQUIRED now) |
| NOAA ONI | avg ~4.3 | Climate/ENSO predictor | YES (free, unverified-independent, seasonal) |
| NASA POWER | avg ~3.9 | Supplementary + validation (T2M/RH/PS vs ERA5) | YES as cross-check; NOT as primary predictor |

## 3. What is NOT recommended
- Using NASA POWER PRECTOTCORR as rainfall "truth" (model-adjusted MERRA-2 precip, not gauge-verified).
- Using CHIRPS as the sole label (satellite blend; use IMD as label, CHIRPS as validation).
- Using ERA5 precipitation for labels (single-level model scheme). ERA5 precip kept only as a feature.

## 4. Final layer assignments (pending TRAINING_DATA_DESIGN approval)
- Labels: IMD 0.25 daily rainfall -> block-nearest cell.
- Predictors: ERA5 atmosphere (primary), CHIRPS rain continuity, NASA POWER met variety, NOAA ONI ENSO context.
- Validation: CHIRPS 0.05 vs IMD 0.25 cross-check + NASA POWER T2M cross-check.
- All download/checksum/metadata recorded (data/metadata/*.json, data/checksums.csv, reports/DATA_DOWNLOAD_LOG.md).