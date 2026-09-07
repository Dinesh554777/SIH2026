# PHASE H — VALIDATION RESULTS (2022–2023)

Date: 2026-09-07 · Seed 42

All metrics below are **VALIDATION 2022–2023** unless marked TEST.

## Validation event rarity (2022–2023)

| Target | positive rate | n_pos |
| ------ | ------------: | ----: |
| onset  | 0.0080 | 592 |
| break  | 0.3232 | 23,976 |
| revival | 0.0290 | 2,149 |
| dry_spell | 0.2038 | 15,114 |

Onset and revival are rare (early-onset days / revival days). Break and dry-spell are
common. Metrics emphasize Brier + PR-AUC + calibration for the rare targets.

## Per-group validation metrics (all models)

### onset
| Group | Model | Brier | PR-AUC | ROC-AUC | Precision | Recall | F1 | ECE |
| ----- | ----- | -----: | -----: | ------: | --------: | -----: | --: | --: |
| A | xgboost | 0.00941 | 0.533 | 0.992 | 0.809 | 0.610 | 0.695 | 0.010 |
| B | xgboost | 0.00894 | 0.520 | 0.992 | 0.808 | 0.620 | 0.701 | 0.009 |
| C | xgboost | 0.00888 | 0.547 | 0.992 | 0.807 | 0.622 | 0.702 | 0.010 |
| D | xgboost | 0.00913 | 0.500 | 0.992 | 0.813 | 0.604 | 0.693 | 0.010 |
| E | xgboost | 0.00905 | 0.524 | 0.992 | 0.809 | 0.617 | 0.700 | 0.010 |
| REF | persistence | **0.00792** | 0.008 | 0.508 | 0.000 | 0.000 | 0.000 | 0.000 |

### break
| Group | Model | Brier | PR-AUC | ROC-AUC | Precision | Recall | F1 | ECE |
| ----- | ----- | -----: | -----: | ------: | --------: | -----: | --: | --: |
| B | xgboost | 0.07900 | 0.927 | 0.963 | 0.700 | 0.820 | 0.756 | 0.040 |
| A | xgboost | 0.08196 | 0.923 | 0.960 | 0.695 | 0.818 | 0.751 | 0.043 |
| REF | persistence | **0.05566** | 0.854 | 0.932 | 0.870 | 0.941 | 0.904 | 0.002 |

### revival (rare)
| Group | Model | Brier | PR-AUC | ROC-AUC | Precision | Recall | F1 | ECE |
| ----- | ----- | -----: | -----: | ------: | --------: | -----: | --: | --: |
| A | xgboost (frozen) | 0.01226 | 0.906 | 0.997 | 0.757 | 0.925 | 0.833 | 0.013 |
| **B** | **xgboost** | **0.00806** | **0.949** | **0.998** | 0.783 | 0.974 | 0.868 | **0.008** |
| C | xgboost | 0.01236 | 0.905 | 0.997 | 0.757 | 0.925 | 0.833 | 0.013 |
| D | xgboost | 0.01068 | 0.929 | 0.997 | 0.778 | 0.945 | 0.853 | 0.012 |
| E | xgboost | 0.01236 | 0.904 | 0.997 | 0.757 | 0.925 | 0.832 | 0.013 |

### dry_spell
| Group | Model | Brier | PR-AUC | ROC-AUC | Precision | Recall | F1 | ECE |
| ----- | ----- | -----: | -----: | ------: | --------: | -----: | --: | --: |
| B | xgboost | 0.07679 | 0.864 | 0.956 | 0.622 | 0.768 | 0.687 | 0.053 |
| A | xgboost | 0.07870 | 0.863 | 0.955 | 0.624 | 0.772 | 0.690 | 0.057 |
| REF | persistence | **0.03340** | 0.852 | 0.945 | 0.799 | 0.913 | 0.852 | 0.002 |

## Frozen-reference comparison (primary gate)

| Target | Frozen ref | Best candidate | ΔBrier (cand − ref) | Decision |
| ------ | ---------- | -------------- | -------------------: | -------- |
| onset | persistence 0.00792 | C/xgb 0.00888 | +0.00096 | keep frozen |
| break | persistence 0.05566 | B/xgb 0.07900 | +0.02334 | keep frozen |
| revival | XGB D_full 0.01226 | **B/xgb 0.00806** | **−0.00420** | **candidate** |
| dry_spell | persistence 0.03340 | B/xgb 0.07679 | +0.04339 | keep frozen |

Only revival shows a meaningful, calibrated validation improvement.
