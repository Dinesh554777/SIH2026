# Phase H — Feature Engineering Report

Status: **COMPLETE — ready for H5 (validation modeling) approval gate**
Date: 2026-09-07

---

## 1. Matrix

| Property        | Value              |
| --------------- | -----------------: |
| Rows            | 370,880            |
| Columns         | 97                 |
| Original columns | 63                |
| Group A features (frozen Phase G full set) | 51 |
| New representation features | 34 |
| Cells           | 304                |
| Seasons         | 2015–2024 (JJAS)   |

Output artifact: `data/processed/phase_h_matrix.parquet`

## 2. Feature groups

| Group          | Prefix | Count | Source      |
| -------------- | ------ | ----: | ----------- |
| Phase G frozen (Group A) | `imd_/chirps_/nasa_/oni_` + context | 51 | IMD, CHIRPS, NASA, ONI, grid |
| H1 Temporal    | `th_`  | 13    | IMD rainfall |
| H2 Seasonal    | `sh_`  | 6     | IMD rainfall + train climatology |
| H3 Event State | `es_`  | 9     | IMD rainfall |
| H4 Spatial     | `sp_`  | 6     | IMD rainfall (0.25° 8-neighbour) |

Group A is exactly the 51 frozen Phase G full-set predictors (`feature_columns()`).
Verified programmatically: count = 51, and no `th_/sh_/es_/sp_` column is a member.
`D_full` in Phase G = the same 51-column list, so Group A reproduces the frozen
full-feature configuration without modification.

## 3. Missingness

| Feature          | NaNs | Cause                                                        | Type            |
| ---------------- | ----: | ------------------------------------------------------------ | --------------- |
| `th_rstd7`       | 3040 | 1 row per (cell, season): first day has <2 obs for a std     | expected boundary |
| `th_rstd14`      | 3040 | same                                                          | expected boundary |
| `sp_mean_lag1`   | 3040 | first date of each season has no previous date                | expected boundary |

3040 = 304 cells × 10 seasons. All are causal/structural boundary NaNs, present **only**
on the first day of each season (June 1). No unexpected NaN found. Group A has 0 NaN.

**Implication for H5:** logistic/RF/XGB require NaN-free arrays. The H5 design must state
an explicit (train-only) imputation rule for these three features — no silent handling.

## 4. Constant features

None (zero-variance columns: 0).

## 5. Duplicate features

Four exact-duplicate pairs across groups (same mathematical definition, genuinely
redundant, not an error):

| Pair |
| ---- |
| `th_wetcount7` = `es_wet_days7` |
| `th_wetcount14` = `es_wet_days14` |
| `th_wet_streak` = `es_wet_duration` |
| `th_dry_streak` = `es_dry_duration` |

Interpretation note for ablation: Groups B (temporal) and D (event-state) therefore
share 4 identical columns. Adding B vs D to A should be read as: B's increment includes
these 4 + 9 unique temporal; D's increment includes these 4 + 5 unique event-state.
The 4 shared columns do not confound either increment **relative to A**.

## 6. Leakage

| Check                              | Result |
| ---------------------------------- | ------ |
| New features equal any target column | none  |
| New features equal any event-date col (`onset_date`) | none |
| Event-date columns in Group A       | none  |
| Feature builders reference label/event-date names | none |
| Future rainfall in rolling/spatial  | none  |

Sub-checks:
- **Temporal/event-state**: all rolling/streak/acceleration computations are causal
  (information at or before `t` only). Tested against hand-computed references on
  random cells/dates; helper resets at `(cell_id, year)` boundaries.
- **Seasonal**: `sh_z`, `sh_clim_pctile`, `sh_onset_prox` derive from doy-mean/std and a
  per-doy pooled ECDF built **on 2015–2021 only**. Lookup uses only training observations
  for each day-of-season. Val/test never enter the reference distributions.
- **Spatial**: same-date neighbour context (contemporaneous observation). `sp_mean_lag1`
  uses only the previous date and resets at season boundary; no cross-year carry-over.
  Neighbour map = 8-neighbour on the 0.25° grid, centre cell excluded, boundary cells have
  fewer neighbours, deterministic, and no row add/loss.

## 7. Ordering / row identity

Both original and Phase H matrices are sorted by `(cell_id, date)`; asserted programmatically:

* same row count (370,880)
* no duplicated `(cell_id, date)`
* identical `(cell_id, date)` sequence between original and Phase H

## 8. Climatology (train-only fitting)

* Climatological onset: first dseason where the train-mean 3-day rainfall sum >= 20 mm
  (rainfall-only; **not** the wettest day, **no** label use). Result: doy 221, dseason 70.
* `sh_z` = (rain − train-mean)/train-std per doy.
* `sh_clim_pctile` = empirical percentile of current rain within that doy's TRAIN-only
  pooled distribution (range observed 0.33–1.00).
* `sh_onset_prox` = climatological-onset doy − current doy.
* `sh_peak_prox` = 213 − current doy (fixed mid-season anchor, JJAS day-of-year math).

## 9. Determinism

Full rebuild (deleting output and re-running assembly) produced identical
shape/columns and exactly equal new-feature values. Determinism: PASS.

## 10. Automated tests

`tests/test_phase_h_features.py` — 11 tests, all pass (`pytest -q`):

| # | Test |
| - | ---- |
| 1 | row identity (`(cell_id,date)`) identical to original |
| 2 | ordering identical (sorted by cell_id → date) |
| 3 | no duplicate `(cell_id,date)` |
| 4 | temporal features causal (hand-computed reference values) |
| 5 | climatology train-only (pooled ECDF contains only train obs) |
| 6 | no label/event-date leakage into features |
| 7 | spatial features preserve row identity (no add/loss) |
| 8 | deterministic rebuild (run twice → identical) |
| 9 | chronological splits train 2015–2021 / val 2022–2023 / test 2024 |
| 10 | group partition correct (prefixes, no overlap, no new-prefix in A) |
| 11 | no future information in the assembled matrix (year-aware spot check) |

## 11. Feature manifest

`reports/PHASE_H_FEATURE_MANIFEST.json` — generated from the implementation; every
feature has name, group, source, prediction-time availability, and train-only-stats flag
(85 entries: 51 Group A + 34 new).

## 12. Known items to resolve at the H5 gate

1. Explicit train-only imputation rule for `th_rstd7`, `th_rstd14`, `sp_mean_lag1`
   (boundary NaNs) — to be stated in FREEZE_H rationale, no silent imputation.
2. Group B/D intentional overlap of 4 duplicate features — already documented above.

---

## Conclusion

The Phase H matrix is assembled and validated: row identity ✓, ordering ✓, no duplicates ✓,
causal ✓, train-only climatology ✓, no target leakage ✓, determinism ✓, pytest ✓.

**READY FOR HUMAN APPROVAL TO BEGIN H5 GROUP ABLATION (validation 2022–2023 only; 2024 untouched).**