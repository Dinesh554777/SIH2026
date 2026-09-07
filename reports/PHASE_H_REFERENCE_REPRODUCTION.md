# PHASE H — REFERENCE REPRODUCTION (H0)

Generated 2026-09-07 · seed 42 · `src/modeling/phase_h/reference_repro.py`

## Purpose

Confirm that the frozen Phase G validation results are reproducible from the frozen
artifacts **before** any Phase H feature engineering. No 2024 labels were touched.

## Method

- Load `data/processed/training_matrix.parquet`.
- Use the exact frozen Phase G feature set: `feature_columns()` → **51 features**
  (24 IMD + 5 CHIRPS + 16 NASA + 2 ONI + lat/lon/doy/dseason).
- Reload the frozen Phase G model archives (`models/{logistic,random_forest,xgboost}/{target}/model.joblib`)
  and the StandardScaler for logistic.
- Predict on the **validation split (2022–2023)** only.
- Recompute Brier (and ROC-AUC) via the same `evaluate.aggregate` used in Phases E–G.
- Persistence reference recomputed from `baseline_predictions.parquet` (validation).

## Result: EXACT REPRODUCTION ✓

### Persistence (frozen reference for onset/break/dry_spell)

| Target | Freeze `val_brier` | Reproduced persistence Brier | Match |
|---|---|---|---|
| onset | 0.0079163 | 0.0079163 | ✓ |
| break | 0.0556558 | 0.0556558 | ✓ |
| dry_spell | 0.0333956 | 0.0333956 | ✓ |

### Revivals (frozen reference = XGBoost full features)

| Target | Freeze `val_brier` | Reproduced XGBoost Brier | Match |
|---|---|---|---|
| revival | 0.0122586 | 0.0122586 | ✓ |

### Full reproduced validation Brier (all ML, 2022–2023)

| Target | logistic | random_forest | xgboost |
|---|---|---|---|
| onset | 0.07346 | 0.01972 | 0.00941 |
| break | 0.13235 | 0.08190 | 0.08196 |
| revival | 0.05263 | 0.01949 | 0.01226 |
| dry_spell | 0.13132 | 0.08197 | 0.07870 |

These match the Phase E–G validation tables to 5 decimal places.

## Frozen Phase G reference (from `FREEZE_G.json`)

- onset → **persistence** (val Brier 0.007916)
- break → **persistence** (val Brier 0.055656)
- dry_spell → **persistence** (val Brier 0.033396)
- revival → **XGBoost, full features** (val Brier 0.012259)

These are the baselines any Phase H candidate must beat **on validation**.

## Conclusion

The frozen reference is fully reproducible. Proceeding to Phase H feature
representations (H1–H4) with the strong Phase G models and persistence as the gate.
