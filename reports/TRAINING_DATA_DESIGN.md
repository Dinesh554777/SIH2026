# TRAINING_DATA_DESIGN

Design of the training/validation/test dataset that the modeling phase will consume.
**Model is NOT trained until this document + DATASET_RECOMMENDATION.md are approved.**

## 1. Target definition (label) — ground truth
- Target: onset/break days of the monsoon at block scale, defined per the problem statement's evapotranspiration
  approach and the onset/break definition in MODELING_PLAN.md / EVALUATION_PLAN.md.
- Operational proxy at data level: daily IMD rainfall (0.25°) mapped to block centroid (nearest cell),
  smoothed over 3-day window to remove dry-out false positives; onset = first date in JJAS window with
  cumulative ≥ threshold sustained rain; break = ≥N consecutive dry days (≤ threshold) after onset.
- If MoES provides village checklists these calibrate the proxy; otherwise the proxy is the label source,
  documented in DATASET_LIMITATIONS.

## 2. Sample construction
- One sample per (distinct-cluster, day) over TRAIN/VAL/TEST, features built from a rolling LAG window
  (e.g., t-1..t-30) of predictors.
- Units: grid cells nearest to block centroids of the 7 pilot districts (Coimbatore, Tiruppur, Erode, Pune,
  Satara, Mandya, Mysuru) — blocks resolved after official GIS boundaries are ingested (currently
  VERIFY_FROM_OFFICIAL_GIS).
- A minimum of N cells per region to balance sample volume; daily samples per cell.

## 3. Feature sets (from downloaded/planned data)
| Block | Source | Variables | Frequency | Note |
| --- | --- | --- | --- | --- |
| ATM | ERA5 | t2m, d2m, mslp, sp, u10, v10, tp | daily (aggregated from hourly) | AUTH_REQUIRED; primary predictors |
| SAT | CHIRPS | precip (0.05) | daily | high-res rain continuity distinct from IMD |
| CLIM | NOAA ONI | ONI anomaly | monthly (3-mo mean) | lag >= 1 season; no target overlap |
| SUPP | NASA POWER | T2M, RH2M, PS, WS10M, PRECTOTCORR | daily | cross-check + extra vars |
| TARGET | IMD | RAINFALL | daily | labels + onset/break derivation |

## 4. Preprocessing rules (agreed, enforced)
- Train-only statistics for all normalization and climatological baselines.
- No use of TEST or VAL dates in any transform fit.
- Missing handling: count NaN% per variable; variables >X% NaN pruned; imputation only with TRAIN stats.
- -999 / missing markers masked (IMD -999; CHIRPS -9999; NASA -999).
- 2024 used ONLY as TEST (never train/val).

## 5. Data files consumed
- data/raw/imd/ind<year>_rfp25.nc (2015-2024)
- data/raw/chirps/chirps_v3.0_rnl_<year>_pilot.nc (2015-2024)
- data/raw/nasa/nasa_power_daily_<param>_b<band>_<year>.csv (2015-2024)
- data/raw/noaa/oni.ascii.txt
- data/raw/era5/ (pending AUTH_REQUIRED download)

## 6. Output artifact
- data/processed/training_features.nc (or parquet) with schema; columns prefixed by block; a
  partition manifest (train/val/test) written next to it; every column tracked back to this doc.

## 7. Acceptance gate
- TRAINING_DATA_DESIGN + DATASET_RECOMMENDATION approved => feature_engineering may proceed.
- Until then the pipeline ends at the data-research deliverables.