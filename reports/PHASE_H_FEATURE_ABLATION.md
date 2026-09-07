# PHASE H — FEATURE ABLATION REPORT

Date: 2026-09-07 · Seed 42

## Design

Phase H tests whether new feature representations (H1 temporal, H2 seasonal, H3 event-state,
H4 spatial) improve on the frozen Phase G architecture. Groups:

| Group | Base | New features | # features |
| ----- | ---- | ------------ | ---------: |
| A | frozen Phase G full | — | 51 |
| B | A + H1 temporal (`th_*`) | 13 | 64 |
| C | A + H2 seasonal (`sh_*`) | 6 | 57 |
| D | A + H3 event-state (`es_*`) | 9 | 60 |
| E | A + H4 spatial (`sp_*`) | 6 | 57 |

All models (logistic, random forest, XGBoost) fitted on TRAIN (2015–2021) only, with
hyperparameters identical to Phases E–G. Structural boundary NaNs
(`th_rstd7`, `th_rstd14`, `sp_mean_lag1`) handled by explicit **train-only median
imputation** — no rows dropped, same frozen statistic for val/test.

## Validation Brier by group (2022–2023)

Frozen reference line (per target) is the actual Phase G frozen winner.

| Target | Group | Logistic | RandomForest | XGBoost | Frozen ref (persistence/XGB) |
| ------ | ----- | --------: | -----------: | ------: | ----------------------------: |
| onset  | A | 0.07346 | 0.01972 | 0.00941 | 0.00792 (persistence) |
| onset  | B | 0.06546 | 0.01988 | **0.00894** | |
| onset  | C | 0.07132 | 0.01876 | 0.00888 | |
| onset  | D | 0.06140 | 0.01987 | 0.00913 | |
| onset  | E | 0.07328 | 0.01977 | 0.00905 | |
| break  | A | 0.13235 | 0.08190 | 0.08196 | 0.05566 (persistence) |
| break  | B | 0.12779 | 0.08060 | **0.07900** | |
| break  | C | 0.13179 | 0.08216 | 0.08197 | |
| break  | D | 0.13042 | 0.08264 | 0.08075 | |
| break  | E | 0.13236 | 0.08257 | 0.08107 | |
| revival| A | 0.05263 | 0.01949 | 0.01226 (frozen) | 0.01226 (XGB D_full) |
| revival| B | 0.04613 | 0.01650 | **0.00806** | |
| revival| C | 0.04851 | 0.02021 | 0.01236 | |
| revival| D | 0.05110 | 0.01881 | 0.01068 | |
| revival| E | 0.05219 | 0.02036 | 0.01236 | |
| dry_spell| A | 0.13132 | 0.08197 | 0.07870 | 0.03340 (persistence) |
| dry_spell| B | 0.12639 | 0.08176 | **0.07679** | |
| dry_spell| C | 0.13045 | 0.08253 | 0.07876 | |
| dry_spell| D | 0.12930 | 0.08256 | 0.07843 | |
| dry_spell| E | 0.13111 | 0.08274 | 0.07785 | |

## Group effect (delta vs frozen reference; negative = better)

| Target | Best group/model | Validation Brier | Δ vs frozen | Improves frozen? |
| ------ | ---------------- | ---------------: | ----------: | ---------------- |
| onset  | C / xgb (best any) | 0.00888 | +0.00096 | **no** (persistence wins) |
| break  | B / xgb | 0.07900 | +0.02334 | **no** (persistence wins) |
| revival| **B / xgb** | **0.00806** | **−0.00420** | **yes** |
| dry_spell | B / xgb | 0.07679 | +0.04339 | **no** (persistence wins) |

## Findings

- **Only temporal features (Group B) materially help any target, and only for revival.**
- For onset, break, dry_spell, no representation (nor any ML model) beats the frozen
  persistence baseline on validation. ML Brier is 2–4× worse than persistence for these.
- Revival: XGBoost + temporal improves validation Brier 0.01226 → 0.00806, PR-AUC
  0.906 → 0.949, ECE 0.013 → 0.008. Seasonal/event-state/spatial do NOT help revival.
- Group F (combined) is NOT constructed — only B helps, and only for revival. Combining
  adds complexity without validation evidence.

## Figures

- `reports/figures/phase_h_feature_ablation.png`
- `reports/figures/phase_h_calibration.png`
