# PHASE G COMPLETION REPORT — FEATURE ABLATION

Generated 2026-09-07T15:19:56Z · seed 42

## Phase G (models trained)

- Configs A_imd, B_imd_chirps, C_imd_chirps_oni fitted on TRAIN only (logistic/RF/XGB, 4 targets, hyperparameters identical to E-F); Config D_full reused from Phase E-F frozen models.
- 51-feature full set, feature groups IMD(24)/CHIRPS(5)/ONI(2)/NASA(16) + context(4).
- Artifacts: `models/ablation/<config>/<target>/<model>/model.joblib` (+scaler for logistic); predictions `data/processed/predictions/ablation/*.parquet`.

## Results

- `onset`: best validation Brier among all ablation configs = 0.0092 (C_imd_chirps_oni/xgboost); baseline min = 0.0079.
- `break`: best validation Brier among all ablation configs = 0.0809 (B_imd_chirps/xgboost); baseline min = 0.0557.
- `revival`: best validation Brier among all ablation configs = 0.0123 (D_full/xgboost); baseline min = 0.0281.
- `dry_spell`: best validation Brier among all ablation configs = 0.0776 (C_imd_chirps_oni/xgboost); baseline min = 0.0334.

Frozen learned winners on validation:

- **revival** frozen D_full/xgboost: test Brier 0.0123, ROC 0.9973, ECE 0.0127

## Test integrity

- 2024 labels opened only after FREEZE_G.json; per-target config chosen on validation only.
- Preprocessing estimated on TRAIN only; no shuffle; chronological splits.

## Findings

- See FEATURE_ABLATION_REPORT.md for the config ladder: whether CHIRPS/ONI/NASA add anything beyond IMD, per target and per model, on validation and test.
- Feature importances (FEATURE_IMPORTANCES.json) list the top features (XGBoost gain) per target.

## Limitations

- 3 evaluation seasons; single test year 2024.
- No feature interactions search; additive group ablation only.
- ERA5 group not included (AUTH_REQUIRED).

## Recommendation

**KEEP SIMPLE BASELINE + REVISIT FEATURES (no Phase H)** — Persistence remains the strongest calibrated baseline for break/dry_spell; ablations quantify which feature groups matter for the rare-event targets (onset/revival). There is no evidence here justifying LSTM/GRU/Transformer (Phase H) — gains would need to exceed these tabular + persistence results, which were not achieved by the strongest tabular models. Focus next on improving the rare-event feature representation and, for break/dry_spell, closing the gap to persistence if desired.
