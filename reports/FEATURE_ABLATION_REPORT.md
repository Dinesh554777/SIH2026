# FEATURE ABLATION REPORT (Phase G)

Generated 2026-09-07T15:19:56Z · seed 42

## Design

Configs share lat/lon/doy/dseason context. All fitted on TRAIN (2015-2021), identical hyperparameters to Phases E-F, validation = 2022-2023. Config D is the Phase E-F frozen reference (no refit).

| Config | Feature groups | # features |
|---|---|---|
| A_imd | IMD | 28 |
| B_imd_chirps | IMD + CHIRPS | 33 |
| C_imd_chirps_oni | IMD + CHIRPS + ONI | 35 |
| D_full | + NASA (full matrix) | 51 |

**How to read ΔBrier**: negative = worse than previous config; positive = improvement. Brier lower = better in all cells.

## Frozen per-target configs (validation only)

| Target | Config | Model | Kind |
|---|---|---|---|
| onset | persistence | persistence | baseline |
| break | persistence | persistence | baseline |
| revival | D_full | xgboost | learned |
| dry_spell | persistence | persistence | baseline |

## Per-target ablation

## Target: `onset`

### Validation (2022-2023)

| Config | Model | Brier | ROC-AUC | PR-AUC | F1 | ECE |
|---|---|---|---|---|---|---|
| A: IMD only (28) | logistic | 0.0733 | 0.9722 | 0.1902 | 0.1294 | 0.1173 |
| A: IMD only (28) | random_forest | 0.0199 | 0.9911 | 0.4121 | 0.3467 | 0.0310 |
| A: IMD only (28) | xgboost | 0.0108 | 0.9920 | 0.4711 | 0.4628 | 0.0118 |
| B: A + CHIRPS (33) | logistic | 0.0721 | 0.9720 | 0.1878 | 0.1315 | 0.1151 |
| B: A + CHIRPS (33) | random_forest | 0.0198 | 0.9912 | 0.4551 | 0.3426 | 0.0323 |
| B: A + CHIRPS (33) | xgboost | 0.0093 | 0.9929 | 0.5178 | 0.5005 | 0.0103 |
| C: B + ONI (35) | logistic | 0.0743 | 0.9720 | 0.1878 | 0.1285 | 0.1180 |
| C: B + ONI (35) | random_forest | 0.0196 | 0.9909 | 0.4452 | 0.3436 | 0.0332 |
| C: B + ONI (35) | xgboost | 0.0092 | 0.9923 | 0.5086 | 0.4916 | 0.0100 |
| D: full (51, E/F ref) | logistic | 0.0735 | 0.9719 | 0.1926 | 0.1291 | 0.1167 |
| D: full (51, E/F ref) | random_forest | 0.0197 | 0.9903 | 0.4529 | 0.3373 | 0.0338 |
| D: full (51, E/F ref) | xgboost | 0.0094 | 0.9923 | 0.5329 | 0.4931 | 0.0104 |
| climatology (baseline) | — | 0.0091 | 0.5475 | 0.0124 | — | 0.0137 |
| persistence (baseline) | — | 0.0079 | 0.5082 | 0.0081 | — | 0.0001 |

### Does adding feature groups change validation Brier?

- **logistic**: best config B_imd_chirps Brier=0.0721 (does NOT beat climatology; does NOT beat persistence) — config deltas: A_imd→B_imd_chirps Δ=-0.0012 · B_imd_chirps→C_imd_chirps_oni Δ=+0.0022 · C_imd_chirps_oni→D_full Δ=-0.0008
- **random_forest**: best config C_imd_chirps_oni Brier=0.0196 (does NOT beat climatology; does NOT beat persistence) — config deltas: A_imd→B_imd_chirps Δ=-0.0001 · B_imd_chirps→C_imd_chirps_oni Δ=-0.0002 · C_imd_chirps_oni→D_full Δ=+0.0001
- **xgboost**: best config C_imd_chirps_oni Brier=0.0092 (does NOT beat climatology; does NOT beat persistence) — config deltas: A_imd→B_imd_chirps Δ=-0.0014 · B_imd_chirps→C_imd_chirps_oni Δ=-0.0001 · C_imd_chirps_oni→D_full Δ=+0.0002

### Test 2024 (post-freeze; one evaluation pass)

| Config | Model | Brier | ROC-AUC | PR-AUC | F1 | ECE |
|---|---|---|---|---|---|---|
| A: IMD only (28) | logistic | 0.0568 | 0.9804 | 0.2235 | 0.1696 | 0.0896 |
| A: IMD only (28) | random_forest | 0.0173 | 0.9938 | 0.5506 | 0.3908 | 0.0290 |
| A: IMD only (28) | xgboost | 0.0076 | 0.9951 | 0.5543 | 0.5731 | 0.0082 |
| B: A + CHIRPS (33) | logistic | 0.0557 | 0.9807 | 0.2313 | 0.1738 | 0.0878 |
| B: A + CHIRPS (33) | random_forest | 0.0180 | 0.9936 | 0.5743 | 0.3785 | 0.0312 |
| B: A + CHIRPS (33) | xgboost | 0.0080 | 0.9949 | 0.5845 | 0.5477 | 0.0088 |
| C: B + ONI (35) | logistic | 0.0546 | 0.9804 | 0.2291 | 0.1759 | 0.0868 |
| C: B + ONI (35) | random_forest | 0.0177 | 0.9932 | 0.5548 | 0.3811 | 0.0315 |
| C: B + ONI (35) | xgboost | 0.0074 | 0.9949 | 0.6065 | 0.5562 | 0.0077 |
| D: full (51, E/F ref) | logistic | 0.0549 | 0.9813 | 0.2451 | 0.1740 | 0.0856 |
| D: full (51, E/F ref) | random_forest | 0.0182 | 0.9930 | 0.5688 | 0.3730 | 0.0327 |
| D: full (51, E/F ref) | xgboost | 0.0074 | 0.9949 | 0.6017 | 0.5482 | 0.0077 |

### Feature importance (XGBoost gain, full model)

| Rank | Feature | XGB gain |
|---|---|---|
| 1 | `imd_sum3` | 4775 |
| 2 | `imd_max3` | 987 |
| 3 | `imd_cum_jjas` | 954 |
| 4 | `imd_dry3` | 433 |
| 5 | `imd_wet7` | 179 |
| 6 | `imd_wet1` | 162 |
| 7 | `dseason` | 150 |
| 8 | `imd_dry7` | 144 |
| 9 | `doy` | 136 |
| 10 | `imd_sum7` | 136 |
| 11 | `imd_sum14` | 119 |
| 12 | `imd_rain_t` | 117 |
| 13 | `imd_sum30` | 89 |
| 14 | `nasa_RH2M_a7` | 80 |
| 15 | `imd_rain_lag3` | 78 |

## Target: `break`

### Validation (2022-2023)

| Config | Model | Brier | ROC-AUC | PR-AUC | F1 | ECE |
|---|---|---|---|---|---|---|
| A: IMD only (28) | logistic | 0.1416 | 0.8919 | 0.7837 | 0.7140 | 0.0983 |
| A: IMD only (28) | random_forest | 0.0865 | 0.9574 | 0.9179 | 0.8101 | 0.0573 |
| A: IMD only (28) | xgboost | 0.0860 | 0.9569 | 0.9170 | 0.8122 | 0.0486 |
| B: A + CHIRPS (33) | logistic | 0.1406 | 0.8959 | 0.7947 | 0.7180 | 0.1018 |
| B: A + CHIRPS (33) | random_forest | 0.0826 | 0.9623 | 0.9262 | 0.8239 | 0.0607 |
| B: A + CHIRPS (33) | xgboost | 0.0809 | 0.9619 | 0.9257 | 0.8272 | 0.0456 |
| C: B + ONI (35) | logistic | 0.1413 | 0.8970 | 0.7988 | 0.7151 | 0.1047 |
| C: B + ONI (35) | random_forest | 0.0832 | 0.9618 | 0.9250 | 0.8231 | 0.0632 |
| C: B + ONI (35) | xgboost | 0.0826 | 0.9593 | 0.9207 | 0.8219 | 0.0424 |
| D: full (51, E/F ref) | logistic | 0.1323 | 0.9034 | 0.8079 | 0.7366 | 0.0906 |
| D: full (51, E/F ref) | random_forest | 0.0819 | 0.9610 | 0.9218 | 0.8235 | 0.0578 |
| D: full (51, E/F ref) | xgboost | 0.0820 | 0.9603 | 0.9227 | 0.8257 | 0.0432 |
| climatology (baseline) | — | 0.2113 | 0.6717 | 0.4450 | — | 0.0865 |
| persistence (baseline) | — | 0.0557 | 0.9317 | 0.8544 | — | 0.0018 |

### Does adding feature groups change validation Brier?

- **logistic**: best config D_full Brier=0.1323 (beats climatology(0.2113); does NOT beat persistence) — config deltas: A_imd→B_imd_chirps Δ=-0.0010 · B_imd_chirps→C_imd_chirps_oni Δ=+0.0006 · C_imd_chirps_oni→D_full Δ=-0.0089
- **random_forest**: best config D_full Brier=0.0819 (beats climatology(0.2113); does NOT beat persistence) — config deltas: A_imd→B_imd_chirps Δ=-0.0039 · B_imd_chirps→C_imd_chirps_oni Δ=+0.0006 · C_imd_chirps_oni→D_full Δ=-0.0013
- **xgboost**: best config B_imd_chirps Brier=0.0809 (beats climatology(0.2113); does NOT beat persistence) — config deltas: A_imd→B_imd_chirps Δ=-0.0051 · B_imd_chirps→C_imd_chirps_oni Δ=+0.0017 · C_imd_chirps_oni→D_full Δ=-0.0007

### Test 2024 (post-freeze; one evaluation pass)

| Config | Model | Brier | ROC-AUC | PR-AUC | F1 | ECE |
|---|---|---|---|---|---|---|
| A: IMD only (28) | logistic | 0.1257 | 0.9008 | 0.8476 | 0.7919 | 0.0160 |
| A: IMD only (28) | random_forest | 0.0848 | 0.9576 | 0.9437 | 0.8582 | 0.0345 |
| A: IMD only (28) | xgboost | 0.0889 | 0.9540 | 0.9400 | 0.8506 | 0.0332 |
| B: A + CHIRPS (33) | logistic | 0.1224 | 0.9058 | 0.8556 | 0.7985 | 0.0155 |
| B: A + CHIRPS (33) | random_forest | 0.0823 | 0.9604 | 0.9461 | 0.8667 | 0.0385 |
| B: A + CHIRPS (33) | xgboost | 0.0847 | 0.9593 | 0.9466 | 0.8592 | 0.0349 |
| C: B + ONI (35) | logistic | 0.1225 | 0.9060 | 0.8560 | 0.8002 | 0.0181 |
| C: B + ONI (35) | random_forest | 0.0836 | 0.9588 | 0.9438 | 0.8652 | 0.0369 |
| C: B + ONI (35) | xgboost | 0.0904 | 0.9539 | 0.9393 | 0.8521 | 0.0398 |
| D: full (51, E/F ref) | logistic | 0.1151 | 0.9157 | 0.8679 | 0.8173 | 0.0165 |
| D: full (51, E/F ref) | random_forest | 0.0830 | 0.9584 | 0.9424 | 0.8672 | 0.0351 |
| D: full (51, E/F ref) | xgboost | 0.0864 | 0.9575 | 0.9437 | 0.8606 | 0.0351 |

### Feature importance (XGBoost gain, full model)

| Rank | Feature | XGB gain |
|---|---|---|
| 1 | `imd_rain_t` | 3706 |
| 2 | `imd_wet1` | 2564 |
| 3 | `imd_max3` | 471 |
| 4 | `imd_cum_jjas` | 388 |
| 5 | `imd_consec_dry` | 157 |
| 6 | `imd_sum3` | 152 |
| 7 | `imd_rain_lag3` | 150 |
| 8 | `chirps_rain` | 148 |
| 9 | `dseason` | 115 |
| 10 | `imd_rain_lag1` | 72 |
| 11 | `imd_dry3` | 64 |
| 12 | `imd_sum30` | 63 |
| 13 | `nasa_WS10M_t` | 60 |
| 14 | `imd_anom_t` | 48 |
| 15 | `doy` | 47 |

## Target: `revival`

### Validation (2022-2023)

| Config | Model | Brier | ROC-AUC | PR-AUC | F1 | ECE |
|---|---|---|---|---|---|---|
| A: IMD only (28) | logistic | 0.0550 | 0.9833 | 0.5911 | 0.4341 | 0.0684 |
| A: IMD only (28) | random_forest | 0.0193 | 0.9959 | 0.8826 | 0.6860 | 0.0278 |
| A: IMD only (28) | xgboost | 0.0127 | 0.9969 | 0.9104 | 0.7661 | 0.0137 |
| B: A + CHIRPS (33) | logistic | 0.0547 | 0.9834 | 0.5932 | 0.4364 | 0.0678 |
| B: A + CHIRPS (33) | random_forest | 0.0195 | 0.9956 | 0.8729 | 0.6854 | 0.0298 |
| B: A + CHIRPS (33) | xgboost | 0.0124 | 0.9969 | 0.9090 | 0.7714 | 0.0132 |
| C: B + ONI (35) | logistic | 0.0553 | 0.9834 | 0.5935 | 0.4337 | 0.0687 |
| C: B + ONI (35) | random_forest | 0.0197 | 0.9950 | 0.8434 | 0.6789 | 0.0302 |
| C: B + ONI (35) | xgboost | 0.0123 | 0.9969 | 0.9086 | 0.7734 | 0.0131 |
| D: full (51, E/F ref) | logistic | 0.0526 | 0.9841 | 0.5980 | 0.4431 | 0.0660 |
| D: full (51, E/F ref) | random_forest | 0.0195 | 0.9950 | 0.8415 | 0.6840 | 0.0303 |
| D: full (51, E/F ref) | xgboost | 0.0123 | 0.9968 | 0.9063 | 0.7704 | 0.0130 |
| climatology (baseline) | — | 0.0320 | 0.5284 | 0.0310 | — | 0.0450 |
| persistence (baseline) | — | 0.0281 | 0.5190 | 0.0301 | — | 0.0012 |

### Does adding feature groups change validation Brier?

- **logistic**: best config D_full Brier=0.0526 (does NOT beat climatology; does NOT beat persistence) — config deltas: A_imd→B_imd_chirps Δ=-0.0004 · B_imd_chirps→C_imd_chirps_oni Δ=+0.0006 · C_imd_chirps_oni→D_full Δ=-0.0027
- **random_forest**: best config A_imd Brier=0.0193 (beats climatology(0.0320); beats persistence(0.0281)) — config deltas: A_imd→B_imd_chirps Δ=+0.0003 · B_imd_chirps→C_imd_chirps_oni Δ=+0.0002 · C_imd_chirps_oni→D_full Δ=-0.0002
- **xgboost**: best config D_full Brier=0.0123 (beats climatology(0.0320); beats persistence(0.0281)) — config deltas: A_imd→B_imd_chirps Δ=-0.0004 · B_imd_chirps→C_imd_chirps_oni Δ=-0.0001 · C_imd_chirps_oni→D_full Δ=-0.0000

### Test 2024 (post-freeze; one evaluation pass)

| Config | Model | Brier | ROC-AUC | PR-AUC | F1 | ECE |
|---|---|---|---|---|---|---|
| A: IMD only (28) | logistic | 0.0522 | 0.9834 | 0.6563 | 0.5139 | 0.0644 |
| A: IMD only (28) | random_forest | 0.0182 | 0.9964 | 0.9153 | 0.7440 | 0.0257 |
| A: IMD only (28) | xgboost | 0.0126 | 0.9976 | 0.9440 | 0.8119 | 0.0136 |
| B: A + CHIRPS (33) | logistic | 0.0519 | 0.9834 | 0.6572 | 0.5151 | 0.0638 |
| B: A + CHIRPS (33) | random_forest | 0.0185 | 0.9962 | 0.9078 | 0.7434 | 0.0277 |
| B: A + CHIRPS (33) | xgboost | 0.0126 | 0.9975 | 0.9410 | 0.8141 | 0.0135 |
| C: B + ONI (35) | logistic | 0.0520 | 0.9834 | 0.6588 | 0.5135 | 0.0642 |
| C: B + ONI (35) | random_forest | 0.0187 | 0.9961 | 0.9065 | 0.7415 | 0.0279 |
| C: B + ONI (35) | xgboost | 0.0124 | 0.9975 | 0.9422 | 0.8092 | 0.0133 |
| D: full (51, E/F ref) | logistic | 0.0501 | 0.9839 | 0.6644 | 0.5198 | 0.0620 |
| D: full (51, E/F ref) | random_forest | 0.0185 | 0.9959 | 0.9000 | 0.7432 | 0.0281 |
| D: full (51, E/F ref) | xgboost | 0.0123 | 0.9973 | 0.9392 | 0.8119 | 0.0127 |

### Feature importance (XGBoost gain, full model)

| Rank | Feature | XGB gain |
|---|---|---|
| 1 | `imd_consec_dry` | 34179 |
| 2 | `imd_wet1` | 8494 |
| 3 | `imd_rain_t` | 3095 |
| 4 | `imd_rain_lag1` | 2394 |
| 5 | `imd_rain_lag3` | 789 |
| 6 | `imd_wet7` | 259 |
| 7 | `imd_dry7` | 180 |
| 8 | `imd_cum_jjas` | 146 |
| 9 | `imd_days_since_wet` | 114 |
| 10 | `imd_sum7` | 90 |
| 11 | `imd_wet3` | 81 |
| 12 | `imd_sum3` | 80 |
| 13 | `imd_max3` | 79 |
| 14 | `dseason` | 68 |
| 15 | `imd_anom_t` | 29 |

## Target: `dry_spell`

### Validation (2022-2023)

| Config | Model | Brier | ROC-AUC | PR-AUC | F1 | ECE |
|---|---|---|---|---|---|---|
| A: IMD only (28) | logistic | 0.1439 | 0.8988 | 0.7007 | 0.5899 | 0.1489 |
| A: IMD only (28) | random_forest | 0.0907 | 0.9510 | 0.8518 | 0.7161 | 0.0909 |
| A: IMD only (28) | xgboost | 0.0875 | 0.9496 | 0.8468 | 0.7198 | 0.0720 |
| B: A + CHIRPS (33) | logistic | 0.1433 | 0.9036 | 0.7142 | 0.5986 | 0.1507 |
| B: A + CHIRPS (33) | random_forest | 0.0854 | 0.9574 | 0.8668 | 0.7360 | 0.0894 |
| B: A + CHIRPS (33) | xgboost | 0.0812 | 0.9568 | 0.8644 | 0.7443 | 0.0673 |
| C: B + ONI (35) | logistic | 0.1433 | 0.9042 | 0.7172 | 0.5977 | 0.1510 |
| C: B + ONI (35) | random_forest | 0.0846 | 0.9572 | 0.8657 | 0.7385 | 0.0882 |
| C: B + ONI (35) | xgboost | 0.0776 | 0.9562 | 0.8626 | 0.7477 | 0.0572 |
| D: full (51, E/F ref) | logistic | 0.1313 | 0.9096 | 0.7214 | 0.6350 | 0.1338 |
| D: full (51, E/F ref) | random_forest | 0.0820 | 0.9555 | 0.8621 | 0.7409 | 0.0793 |
| D: full (51, E/F ref) | xgboost | 0.0787 | 0.9551 | 0.8626 | 0.7442 | 0.0566 |
| climatology (baseline) | — | 0.1608 | 0.6608 | 0.2944 | — | 0.0728 |
| persistence (baseline) | — | 0.0334 | 0.9454 | 0.8523 | — | 0.0018 |

### Does adding feature groups change validation Brier?

- **logistic**: best config D_full Brier=0.1313 (beats climatology(0.1608); does NOT beat persistence) — config deltas: A_imd→B_imd_chirps Δ=-0.0006 · B_imd_chirps→C_imd_chirps_oni Δ=-0.0000 · C_imd_chirps_oni→D_full Δ=-0.0120
- **random_forest**: best config D_full Brier=0.0820 (beats climatology(0.1608); does NOT beat persistence) — config deltas: A_imd→B_imd_chirps Δ=-0.0054 · B_imd_chirps→C_imd_chirps_oni Δ=-0.0008 · C_imd_chirps_oni→D_full Δ=-0.0026
- **xgboost**: best config C_imd_chirps_oni Brier=0.0776 (beats climatology(0.1608); does NOT beat persistence) — config deltas: A_imd→B_imd_chirps Δ=-0.0063 · B_imd_chirps→C_imd_chirps_oni Δ=-0.0036 · C_imd_chirps_oni→D_full Δ=+0.0011

### Test 2024 (post-freeze; one evaluation pass)

| Config | Model | Brier | ROC-AUC | PR-AUC | F1 | ECE |
|---|---|---|---|---|---|---|
| A: IMD only (28) | logistic | 0.1265 | 0.9089 | 0.7531 | 0.6987 | 0.0935 |
| A: IMD only (28) | random_forest | 0.0944 | 0.9513 | 0.8841 | 0.7629 | 0.0806 |
| A: IMD only (28) | xgboost | 0.0961 | 0.9462 | 0.8759 | 0.7529 | 0.0713 |
| B: A + CHIRPS (33) | logistic | 0.1228 | 0.9147 | 0.7687 | 0.7117 | 0.0933 |
| B: A + CHIRPS (33) | random_forest | 0.0893 | 0.9560 | 0.8915 | 0.7783 | 0.0769 |
| B: A + CHIRPS (33) | xgboost | 0.0897 | 0.9537 | 0.8910 | 0.7733 | 0.0687 |
| C: B + ONI (35) | logistic | 0.1238 | 0.9146 | 0.7693 | 0.7107 | 0.0958 |
| C: B + ONI (35) | random_forest | 0.0899 | 0.9539 | 0.8874 | 0.7748 | 0.0747 |
| C: B + ONI (35) | xgboost | 0.0949 | 0.9438 | 0.8695 | 0.7546 | 0.0604 |
| D: full (51, E/F ref) | logistic | 0.1151 | 0.9245 | 0.7889 | 0.7282 | 0.0857 |
| D: full (51, E/F ref) | random_forest | 0.0878 | 0.9540 | 0.8868 | 0.7760 | 0.0689 |
| D: full (51, E/F ref) | xgboost | 0.0923 | 0.9488 | 0.8800 | 0.7640 | 0.0619 |

### Feature importance (XGBoost gain, full model)

| Rank | Feature | XGB gain |
|---|---|---|
| 1 | `imd_dry3` | 33064 |
| 2 | `imd_wet1` | 6329 |
| 3 | `imd_consec_dry` | 2035 |
| 4 | `imd_wet3` | 1233 |
| 5 | `imd_days_since_wet` | 366 |
| 6 | `imd_cum_jjas` | 363 |
| 7 | `imd_rain_t` | 317 |
| 8 | `chirps_rain` | 252 |
| 9 | `imd_wet7` | 202 |
| 10 | `dseason` | 124 |
| 11 | `imd_dry7` | 111 |
| 12 | `nasa_WS10M_t` | 90 |
| 13 | `nasa_RH2M_t` | 82 |
| 14 | `imd_max3` | 80 |
| 15 | `imd_sum3` | 78 |

## Figures

- `reports/figures/ablation_brier_val.png` (see completion report).
