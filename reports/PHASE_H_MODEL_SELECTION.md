# PHASE H — MODEL SELECTION

Date: 2026-09-07 · Seed 42

## Selection rule (H8 / H8.1)

A candidate replaces the frozen reference only if it delivers a **meaningful, stable**
validation improvement with acceptable calibration and generalization, and does not merely
exploit a tiny Brier edge with worse calibration/complexity.

## Per-target decision

| Target | Frozen reference (Phase G) | Best Phase H candidate | Validation Brier (ref → cand) | Decision |
| ------ | -------------------------- | ---------------------- | ----------------------------: | -------- |
| onset | persistence | (none) | 0.00792 → (best ML 0.00888) | **KEEP FROZEN** |
| break | persistence | (none) | 0.05566 → (best ML 0.07900) | **KEEP FROZEN** |
| revival | XGBoost D_full | **XGBoost B (temporal)** | 0.01226 → **0.00806** | **CANDIDATE** |
| dry_spell | persistence | (none) | 0.03340 → (best ML 0.07679) | **KEEP FROZEN** |

## Selection evidence for the revival candidate

Validation (2022–2023):
- Brier 0.01226 → 0.00806 (−34%)
- PR-AUC 0.906 → 0.949
- ECE 0.0130 → 0.0083 (better calibrated)
- ROC-AUC 0.997 → 0.998

Generalization:
- Improves in 2022 (0.0071 vs 0.0114) and 2023 (0.0090 vs 0.0131)
- Improves in TN, MH, KA (regional Brier 0.007–0.009 vs 0.010–0.013; PR-AUC ≈0.93–0.95)
- Event counts healthy (2,149 val positives)

## Why no Group F

Only temporal features (B) improve anything, and only revival. Seasonal/event-state/spatial
added no reliable validation value to any target. Combining groups (F = B+C+D+E) would add
model complexity without validation evidence, violating H8.1. F is therefore **not
constructed**.

## Why persistence is kept for the other three targets

- onset/break/dry_spell: every ML + every representation Brier is materially worse than
  the frozen persistence baseline on validation. Adding learned models would be a regression
  in Brier despite higher discrimination (ROC/PR), and persistence is far better calibrated
  (ECE ~0.002 vs 0.04–0.13) and simpler. No evidence justifies replacement.

## Feature contribution (descriptive; XGBoost gain, revival-B model)

Top contributors with the new representation (top 40 by gain):
- `th_accel` is the #2 overall feature (after `imd_wet1`)
- 12 of the top-40 features are new temporal (`th_*`) features: `th_accel`, `th_dry_streak`,
  `th_sum5`, `th_rmean7`, `th_cv7`, `th_wet_streak`, `th_wetcount7/14`, `th_rstd7`,
  `th_sum21`, `th_sum10`, `th_rmean14`
- Seasonal/event-state/spatial features do not rank among top contributors, consistent with
  their lack of validation impact.

`reports/PHASE_H_FEATURE_IMPORTANCE.md` provides the full ranking.
