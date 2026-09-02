# DATA_LEAKAGE_REPORT

Covers leakage risks at the **data-research stage** of the SIH26086 pipeline (there is no model trained yet;
what is reported below is the leakage *surface* of the downloaded/planned data and the guards that will be
enforced in the ETS - evaluation-training-serve - split).

## 1. Split policy (fixed, never shuffled)

- Config (config/project.yaml): TRAIN 2015-01-01..2021-12-31, VALIDATION 2022-01-01..2023-12-31,
  TEST 2024-01-01..2024-12-31.
- Rule: the full time series is NEVER randomly shuffled; splits are purely chronological.
- Every train/val/test mask is derived from the SAME calendar so a year cannot appear in two sets.

## 2. Known/neutralized leakage paths

| Leak path | Risk | Guard already in place | Status |
| --- | --- | --- | --- |
| CHIRPS includes station precipitation that IMD also uses? (different networks) | LOW - independent providers | report IMD-vs-CHIRPS metrics modulo bias; never blend *labels* from both | documented |
| Downstream feature engineering from TEST data (e.g., climatological normal fitted on 2024) | HIGH if done | feature statistics (baseline climatology, thresholds) fit on TRAIN only | to be enforced in feature_engineering |
| Spatial leakage: neighbours within pilot bbox share the same coarse 0.25/0.5 grid cell | MEDIUM | grid cells map to blocks explicitly; model is trained per-cell or with cell-id to avoid cross-cell label sharing; evaluation per block | to be enforced |
| Aggregating daily->monthly/seasonal across the split boundary | MEDIUM | compute all aggregates INSIDE each split window (padding of lags only from past) | to be enforced |
| ERA5 hourly->daily mean after 2024 | none for test if downloaded once and split AFTER aggregation | acquisition is period-full; splits applied only after dataset assembled | documented |

## 3. Downloads performed & their split-compatibility

- IMD: full 2015-2024 (3653 daily files) — the entire period is stored; splits applied at load time.
- CHIRPS: full 2015-2024 pilot bbox — same.
- NASA POWER: full 2015-2024, same.
- NOAA ONI: seasonal index covering 2015-2024 — same, but note ONI is a *3-month* running mean; a season
  overlaps adjacent months. The FEATURE window (e.g., DJF/NDJ) used for a given day must come from lagged
  calendar months, never from "the month itself of the target" to avoid target-in-feature leakage.
- ERA5: NOT downloaded (AUTH_REQUIRED); when acquired it must be sliced across the same boundary - no issue.

## 4. Deliberate "leak-free" evaluation protocol (for when models exist)

1. Fit transforms (scalers, PCA, climatology baselines, onset/break thresholds) on TRAIN only.
2. Tune only on VALIDATION; final report on TEST 2024 once.
3. Block-level scores computed per block; never report bbox-averaged numbers as block accuracy.
4. Baseline (persistence / climatology) must be defined with TRAIN-ONLY statistics so it cannot "cheat" on TEST.

## 5. Residual risks requiring future action

- CHIRPS v3.0 final daily (rnl chain from 1981) is a *reanalysis+satellite* product; if IMD-daily is chosen
  as ground truth, CHIRPS is used ONLY as predictor/secondary - never as a second label stream.
- NOAA ONI overlap rule (lag >= 1 season) must be encoded in feature_engineering tests.

## Conclusion at data stage

Given chronological splits + TRAIN-only feature statistics + per-block evaluation, the primary leakage
surface is controlled. Two items are flagged as MUST-FIX in feature engineering: (a) TRAIN-only normalisation,
(b) ONI seasonal lag to avoid target overlap.