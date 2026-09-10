# MVP Model Provenance (SIH26086)

Every forecast/advisory/explain response returned by the MVP carries a `provenance`
block (see example below). This document is the human-readable trace of where every
number in the system comes from.

## 1. Freeze File

- **File:** `data/processed/FREEZE_H.json`
- **Role:** single source of truth for the model architecture frozen on
  `2026-09-07T00:00:00Z` (Phase H decision: persist freeze; no 2024 involvement).
- **Runtime digest (sha256, first 16 hex, computed at serve-time):** `4f122044f8710b53`
- **Train/validation/test windows (respectively):** 2015–2021 / 2022–2023 / 2024.
- **Note recorded in the file:** `2024 TEST DATA WAS NOT USED FOR FEATURE SELECTION OR MODEL SELECTION.`

## 2. Per-Target Frozen Specification

| Target | Selected model | Feature group | Frozen decision | Main artifact |
|---|---|---|---|---|
| `onset` | persistence | frozen_reference | KEEP_FROZEN_REFERENCE | baseline |
| `break` | persistence | frozen_reference | KEEP_FROZEN_REFERENCE | baseline |
| `dry_spell` | persistence | frozen_reference | KEEP_FROZEN_REFERENCE | baseline |
| `revival` | XGBoost | B_temporal (64 preds) | CANDIDATE_FOR_FREEZE (frozen 2026-09-07) | `models/phase_h/B/revival/*` |

## 3. Revival Model

- **Artifact directory:** `models/phase_h/B/revival/`
- **Files:** `xgboost.joblib` (XGBClassifier), `imputer.joblib`
  (SimpleImputer, strategy=median), `CONFIG.json` (feature list, statistics,
  hyperparameters).
- **Feature list:** exactly the 64 columns in `CONFIG.json` (51 Group A + 13
  `th_*` temporal features). The feature list and order are asserted against the
  artifact at load time and in `tests/test_mvp_serving.py::test_revival_feature_order_matches_artifact`.
  `sp_mean_lag1` is present in the matrix but is NOT part of the 64 (it was
  removed as a leakage/availability casualty during Phase H).
- **Preprocessing:** SimpleImputer(median) with **train-only** statistics, applied
  at inference time to the (rare) structural NaNs (`th_rstd7`, `th_rstd14`,
  `sp_mean_lag1`-adjacent cells on the first JJAS day). Serving re-applies the same
  frozen statistics; imputer statistics parity is tested.
- **Hyperparameters (frozen):** n_estimators=300, max_depth=6, learning_rate=0.1,
  subsample=0.9, colsample_bytree=0.9, scale_pos_weight=32.12, tree_method=hist, seed=42.
- **Validation (2022–2023):** Brier 0.00806 · PR-AUC 0.9487 · ECE 0.00835.

## 4. Persistence Baselines (onset / break / dry_spell)

- **Definition (unchanged from Phase G/H):** two-state Markov transition
  P(y_t=1 | y_{t-1}) estimated **on train only**; on the first monsoon-scaled day
  of the season (dseason==1) the probability falls back to the cell-dseason
  climatological frequency `build_climatology`.
- **Train transition matrix (as served):**
  - onset: p11=0.0000, p01=0.0082
  - break: p11=0.9078, p01=0.0475
  - dry_spell: p11=0.9165, p01=0.0209
  - revival (not used as persistence; listed for completeness): p11=0.0000, p01=0.0314
- **Validation Brier / ECE:** onset 0.00792 / 6.6·10^-5; break 0.05566 / 0.00183;
  dry_spell 0.03340 / 0.00179.
- Serving is wired to the **same** `build_persistence_transitions` /
  `build_climatology` helpers used at freeze time, and parity against
  `data/processed/predictions/baseline_predictions.parquet` is asserted in tests.

## 5. Data

- **Matrix:** `data/processed/phase_h_matrix.parquet` — 370,880 rows × 97 columns,
  304 pilot grid cells (0.25° regular grid), days Jun 1–Sep 30 (JJAS),
  2015-06-01 … 2024-09-30. Features: IMD rainfall (grid + neighbouring-cell
  aggregates) + derived `th_*` temporal features.
- **Pilot cells by bbox-assigned region:** TN 207 · MH 72 · TN;KA 20 · KA 5.
  TN;KA cells are region-labelled KA (bbox guess is explicitly non-authoritative;
  admin boundary claims are out of MVP scope).
- **Data mode:** `historical/demo` — the MVP serves on-demand inference over the
  frozen matrix; there is no live ingest, so every timestamp is an observation
  timestamp `forecast_date`, not a "now".

## 6. Inference Path (what the API executes)

1. Resolve & validate `(cell_id, date)`.
2. Compute persistence probabilities from the frozen transition table
   (climatology fallback on dseason==1).
3. Compute revival probability: fetch row → frozen median imputation → featurize in
   CONFIG order → `xgboost.predict_proba[:,1]` → apply band.
4. Assemble deterministic rules (v1) → cards, dominant state, current signal,
   sensitivity (frozen model evaluated one feature at a time vs its train median).
5. Stamp provenance + data mode + horizon note; return.

## 7. Example Provenance Block (as served)

```json
{
  "model_version": "FREEZE_H",
  "freeze_file": "data/processed/FREEZE_H.json",
  "freeze_digest": "4f122044f8710b53",
  "data_mode": "historical/demo",
  "targets": {
    "onset":     {"model": "persistence", "feature_group": "frozen_reference"},
    "break":     {"model": "persistence", "feature_group": "frozen_reference"},
    "dry_spell": {"model": "persistence", "feature_group": "frozen_reference"},
    "revival":   {"model": "xgboost", "feature_group": "B_temporal", "n_features": 64,
                  "feature_list_source": "models/phase_h/B/revival/CONFIG.json",
                  "imputation": "SimpleImputer(median), train-only statistics",
                  "seed": 42}
  },
  "note": "2024 TEST DATA WAS NOT USED FOR FEATURE SELECTION OR MODEL SELECTION.",
  "forecast_horizon_note": "Forecast is generated AFTER the day's rainfall observations are available ...",
  "spatial_unit": {"type": "regular_grid_0.25deg", "note": "Pilot grid cell. Not an official village/block boundary."}
}
```