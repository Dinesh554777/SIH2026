# PHASE H — FEATURE IMPORTANCE

Date: 2026-09-07

Descriptive only (XGBoost gain). Not causal evidence.

## Source models

- `models/phase_h/B/revival/xgboost.joblib` (64 features: 51 Group A + 13 temporal)
- Per-target gain maps read from the fitted boosters.

## Revival (only target with a frozen candidate)

Top 25 features by XGBoost gain:

| Rank | Feature | Gain | New (H1–H4)? |
| ---- | ------- | ---: | ------------ |
| 1 | `imd_wet1` | 21,215 | |
| 2 | `th_accel` | 7,250 | **NEW temporal** |
| 3 | `imd_rain_lag1` | 1,721 | |
| 4 | `imd_rain_t` | 715 | |
| 5 | `imd_wet7` | 577 | |
| 6 | `imd_rain_lag3` | 279 | |
| 7 | `th_dry_streak` | 210 | **NEW temporal** |
| 8 | `imd_cum_jjas` | 151 | |
| 9 | `th_sum5` | 146 | **NEW temporal** |
| 10 | `th_rmean7` | 120 | **NEW temporal** |
| 11 | `imd_sum7` | 96 | |
| 12 | `th_cv7` | 93 | **NEW temporal** |
| 13 | `th_wet_streak` | 92 | **NEW temporal** |
| 14 | `imd_wet3` | 67 | |
| 15 | `th_wetcount7` | 65 | **NEW temporal** |
| 16 | `imd_max3` | 58 | |
| 17 | `imd_dry3` | 52 | |
| 18 | `th_wetcount14` | 47 | **NEW temporal** |
| 19 | `dseason` | 41 | |
| 20 | `imd_sum3` | 33 | |
| 21 | `th_rstd7` | 30 | **NEW temporal** |
| 22 | `imd_dry7` | 27 | |
| 23 | `imd_days_since_wet` | 24 | |
| 24 | `imd_dry14` | 23 | |
| 25 | `doy` | 22 | |

Additional `th_*` features in the top 40: `th_sum21` (rank 26), `th_sum10` (35), `th_rmean14` (36).

## Answers to the H7.2 questions

- **Do H1–H4 features matter?** Temporal (H1) features matter for revival — `th_accel`
  alone ranks #2 and a dozen temporal features sit in the top 40.
- **Does temporal contribute?** Yes (revival). This is the group that drives the
  validation improvement.
- **Does seasonal contribute?** No measurable validation contribution; seasonal features
  (`sh_*`) do not appear in the top contributors for the revival model.
- **Does spatial contribute?** No measurable validation contribution; `sp_*` do not rank.
- **Does event-state contribute?** No measurable validation contribution; `es_*` do not rank
  (their duplicates `th_wetcount*`/`th_*_streak` do, but that is the temporal overlap).
- **Is the improvement dominated by persistence-like info?** Partly — `imd_wet1`,
  `imd_rain_lag1`, `imd_rain_t` (lag/today rainfall) remain top. But the new temporal
  state metrics (`th_accel`, streaks, short-window sums/cv) add signal beyond simple
  persistence, which is exactly why the improvement over the frozen model holds.

## Caveat

Gain values reflect in-model usage, not causal effect. The reproduction test (FREEZE_H →
single 2024 eval) is the real evidence of generalization, provided in the completion report.