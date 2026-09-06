# PHASES E–F COMPLETION REPORT

Generated 2026-09-06T14:02:17Z · random seed 42

## Phase E (models trained)

- **Baselines**: climatology `P(target | cell, dseason)` estimated on TRAIN only; persistence (two-state Markov `P(y_t|y_{t-1})` on TRAIN only; `dseason==1` falls back to climatology).
- **Logistic**: StandardScaler fitted on TRAIN only; C=1.0, class_weight=balanced, lbfgs.
- **Random forest**: 250 trees, max_depth 14, min_samples_leaf 20, class_weight=balanced.
- **XGBoost**: 300 trees, depth 6, lr 0.1, subsample/colsample 0.9, scale_pos_weight from TRAIN imbalance.
- Targets: **onset, break, revival, dry_spell** trained independently; class balance documented per split.
- Features: 51 numeric (24 IMD + 5 CHIRPS + 16 NASA + 2 ONI + lat/lon/doy/dseason); no test-derived statistics.
- Artifacts: `models/<model>/<target>/model.joblib` (+ `scaler.joblib` for logistic), `models/CONFIG/*.json`,
  predictions in `data/processed/predictions/`.

## Phase F (evaluation)

- Brier (primary), log loss, ECE + 10-bin reliability, ROC-AUC, PR-AUC, P/R/F1@0.5, confusion matrix.
- Year-by-year (2022, 2023, 2024) and regional (TN/MH/KA, box-derived) breakdowns; delta analysis vs both baselines.
- Figures in `reports/figures/`.

## Test integrity

- 2024 labels opened **only after** `FREEZE.json` was written (selection used validation alone).
- No full-series random shuffle; chronological split used throughout.
- Preprocessing (scaler, climatology, Markov transitions, class weights) estimated on TRAIN only.

## Scientific findings

- Learned-model winners on validation: **1/4 targets** (see MODEL_SELECTION_DECISION.md).
- Best/worst target & model, baseline deltas, calibration, year and region variability are in the companion reports and in `reports/figures/`. Where baselines ≥ ML, this is reported verbatim (no fabricated success).

## Limitations

- Only 3 evaluation seasons (2022-2024) → weak generalization evidence.
- Rare targets (onset, revival) → unstable single-year ROC/PR-AUC.
- No ERA5 (AUTH_REQUIRED); NASA/ONI are supplementary, CHIRPS is cross-check only.
- Admin boundaries not authoritative → box-derived regions only.
- No hyperparameter search by design; conservative defaults.

## Recommendation

**REVISIT FEATURES (and KEEP SIMPLE BASELINE where ML lost)** — Learned models won 1/4 targets on validation; the losing targets need feature/ablation study before any deep-learning investment (Phase G, then revisit).