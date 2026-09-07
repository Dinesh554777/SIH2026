# PHASE H — COMPLETION REPORT

Date: 2026-09-07 · Seed 42

## Final frozen comparison (TEST — 2024 — single post-freeze pass)

| Target | Phase G Frozen | Phase H Frozen | Val Brier (G → H) | Test Brier (G → H) | Test PR-AUC (G → H) | Decision |
| ------ | -------------- | -------------- | ----------------: | -----------------: | -------------------: | -------- |
| onset | Persistence | Persistence (unchanged) | 0.00792 → 0.00792 | 0.00802 → 0.00802 | 0.0082 → 0.0082 | KEEP FROZEN REF |
| break | Persistence | Persistence (unchanged) | 0.05566 → 0.05566 | 0.07032 → 0.07032 | 0.869 → 0.869 | KEEP FROZEN REF |
| revival | XGBoost D_full (51) | **XGBoost B + temporal (64)** | 0.01226 → **0.00806** | 0.01230 → **0.00723** | 0.939 → **0.972** | **IMPROVED** |
| dry_spell | Persistence | Persistence (unchanged) | 0.03340 → 0.03340 | 0.04074 → 0.04074 | 0.865 → 0.865 | KEEP FROZEN REF |

## Full 2024 test metrics for the frozen candidates (TEST — 2024)

| Target | Phase | Model | Brier | PR-AUC | ROC-AUC | Prec | Rec | F1 | ECE |
| ------ | ----- | ----- | -----: | -----: | ------: | ----: | ---: | --: | --: |
| onset | G | persistence | 0.00802 | 0.008 | 0.508 | 0.000 | 0.000 | 0.000 | 0.000 |
| onset | H | persistence | 0.00802 | 0.008 | 0.508 | 0.000 | 0.000 | 0.000 | 0.000 |
| break | G | persistence | 0.07032 | 0.869 | 0.923 | 0.912 | 0.910 | 0.911 | 0.014 |
| break | H | persistence | 0.07032 | 0.869 | 0.923 | 0.912 | 0.910 | 0.911 | 0.014 |
| revival | G | XGB D_full | 0.01230 | 0.939 | 0.997 | 0.702 | 0.962 | 0.812 | 0.013 |
| revival | H | **XGB B** | **0.00723** | **0.972** | **0.999** | **0.808** | 0.970 | **0.882** | **0.007** |
| dry_spell | G | persistence | 0.04074 | 0.865 | 0.945 | 0.919 | 0.918 | 0.918 | 0.007 |
| dry_spell | H | persistence | 0.04074 | 0.865 | 0.945 | 0.919 | 0.918 | 0.918 | 0.007 |

2024 test note: 2024 is a heavy-break year (break positive rate 0.428 test vs 0.323 val),
so absolute Brier for break/dry_spell rises vs validation, consistent across both frozen
architectures. The revival improvement transfers to 2024 (Brier 0.01230 → 0.00723,
PR-AUC 0.939 → 0.972) — a genuine held-out gain, not overfitting to validation.

## Evaluator analysis (10 required answers)

1. **Did temporal features improve anything?** Yes — revival only. XGBoost + `th_*` cuts
   validation Brier 0.01226 → 0.00806 and test Brier → 0.00723.
2. **Did seasonal features improve anything?** No — no target improved with `sh_*`.
3. **Did event-state features improve anything?** No material effect beyond its overlap
   with temporal features (duplicate columns), and worst than B for revival.
4. **Did spatial features improve anything?** No — `sp_*` changed nothing.
5. **Which target benefits from ML?** Revival (rare) benefits from XGBoost + temporal.
6. **Which targets are better handled by persistence?** onset, break, dry_spell — ML is
   2–4× worse in Brier than frozen persistence on validation and test.
7. **Are improvements stable across 2022 and 2023?** Yes — revival-B improves both (2022:
   0.0071 vs 0.0114; 2023: 0.0090 vs 0.0131).
8. **Are improvements geographically stable?** Yes — improves in TN/MH/KA with PR-AUC ≈0.93–0.95.
9. **Is additional complexity justified?** Only for revival (13 extra features, same model
   family, better Brier+calibration). Not for the other three targets (persistence wins).
10. **Final frozen architecture:** persistence for onset/break/dry_spell; XGBoost + temporal
    (Group B, 64 features) for revival. Imputation: train-only median for 3 boundary-NaN
    features. Details in `FREEZE_H.json`.

## Integrity / reproducibility

- 2024 used for decisions at NO point before FREEZE_H.json was written.
- All models fitted on TRAIN (2015–2021) only; splits chronological; no shuffle.
- Imputation (SimpleImputer median) fitted on TRAIN only; identical frozen statistic for
  val/test.
- Single test pass after freeze; no post-test tuning.
- `pytest -q`: 29 passed (11 feature-matrix + 8 Phase H modeling + 10 leakage).
- Determinism: group predictions rebuilt identically; imputer statistics consistent across
  target models.

## Artifacts

- FREEZE: `data/processed/FREEZE_H.json`
- Models: `models/phase_h/<group>/<target>/*.joblib` (+ `CONFIG.json`)
- Predictions: `data/processed/predictions/phase_h/group_{A..E}_train_val.parquet`,
  `val_metrics_all.parquet`, `val_compare_frozen.parquet`, `test_2024_frozen.parquet`
- Reports: this file + PHASE_H_FEATURE_ABLATION.md, PHASE_H_VALIDATION_RESULTS.md,
  PHASE_H_GENERALIZATION_REPORT.md, PHASE_H_MODEL_SELECTION.md, PHASE_H_FEATURE_IMPORTANCE.md,
  PHASE_H_FEATURE_ENGINEERING_REPORT.md
- Figures: `reports/figures/phase_h_feature_ablation.png`, `phase_h_calibration.png`

## Limitations

- Single test year (2024); 3 evaluation seasons available.
- Regional grouping is bbox-derived only (admin not authoritative).
- Onset is very rare (592 val positives) — persistence remains baseline despite ML matching.
- ERA5 not included (AUTH_REQUIRED), consistent with prior phases.

## Decision

**PROCEED_TO_FINAL_MVP** — provisionally. The frozen architecture now is: persistence for
onset/break/dry_spell (unchanged) and XGBoost + temporal features for revival (validated
improvement that transferred to held-out 2024). This is the minimum-change result:
reliable, calibrated, and reproducible — with a narrow, well-evidenced deviation for the one
target where representation clearly matters.