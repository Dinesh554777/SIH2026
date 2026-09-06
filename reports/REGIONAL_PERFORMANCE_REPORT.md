# REGIONAL PERFORMANCE REPORT (Phases E-F)

Generated 2026-09-06T14:02:17Z

## Caveats

**Administrative boundaries are NOT authoritative** (`PENDING_OFFICIAL_GIS`). Regions derive from pilot bounding-box membership (`bbox_guess`) only: TN = 207 cells, MH = 72 cells, KA = 25 cells (incl. 20 overlap `TN;KA`). KA's cell count is small → treat KA columns as descriptive only. Regional numbers are for spotting geographic degradation/robustness, not for strong regional claims.

## Target: `onset`

### val

| Region | Model | n | Brier | ROC-AUC | ECE |
|---|---|---|---|---|---|
| TN | climatology | 50508 | 0.0090 | 0.5459 | 0.0137 |
| TN | persistence | 50508 | 0.0079 | 0.5082 | 0.0000 |
| TN | logistic | 50508 | 0.0754 | 0.9714 | 0.1193 |
| TN | random_forest | 50508 | 0.0214 | 0.9896 | 0.0364 |
| TN | xgboost | 50508 | 0.0099 | 0.9914 | 0.0111 |
| MH | climatology | 17568 | 0.0093 | 0.5556 | 0.0136 |
| MH | persistence | 17568 | 0.0079 | 0.5081 | 0.0001 |
| MH | logistic | 17568 | 0.0677 | 0.9739 | 0.1093 |
| MH | random_forest | 17568 | 0.0158 | 0.9919 | 0.0270 |
| MH | xgboost | 17568 | 0.0084 | 0.9939 | 0.0090 |
| KA | climatology | 6100 | 0.0090 | 0.5374 | 0.0141 |
| KA | persistence | 6100 | 0.0078 | 0.5081 | 0.0002 |
| KA | logistic | 6100 | 0.0736 | 0.9709 | 0.1160 |
| KA | random_forest | 6100 | 0.0173 | 0.9921 | 0.0317 |
| KA | xgboost | 6100 | 0.0085 | 0.9944 | 0.0092 |
### test

| Region | Model | n | Brier | ROC-AUC | ECE |
|---|---|---|---|---|---|
| TN | climatology | 25254 | 0.0083 | 0.6351 | 0.0112 |
| TN | persistence | 25254 | 0.0080 | 0.5082 | 0.0000 |
| TN | logistic | 25254 | 0.0554 | 0.9787 | 0.0868 |
| TN | random_forest | 25254 | 0.0198 | 0.9914 | 0.0350 |
| TN | xgboost | 25254 | 0.0083 | 0.9934 | 0.0082 |
| MH | climatology | 8784 | 0.0095 | 0.5599 | 0.0136 |
| MH | persistence | 8784 | 0.0081 | 0.5083 | 0.0002 |
| MH | logistic | 8784 | 0.0516 | 0.9892 | 0.0771 |
| MH | random_forest | 8784 | 0.0143 | 0.9976 | 0.0278 |
| MH | xgboost | 8784 | 0.0048 | 0.9987 | 0.0065 |
| KA | climatology | 3050 | 0.0084 | 0.6028 | 0.0121 |
| KA | persistence | 3050 | 0.0078 | 0.5081 | 0.0002 |
| KA | logistic | 3050 | 0.0610 | 0.9794 | 0.1005 |
| KA | random_forest | 3050 | 0.0153 | 0.9911 | 0.0275 |
| KA | xgboost | 3050 | 0.0082 | 0.9934 | 0.0082 |

## Target: `break`

### val

| Region | Model | n | Brier | ROC-AUC | ECE |
|---|---|---|---|---|---|
| TN | climatology | 50508 | 0.2209 | 0.6585 | 0.0881 |
| TN | persistence | 50508 | 0.0591 | 0.9301 | 0.0035 |
| TN | logistic | 50508 | 0.1396 | 0.8921 | 0.0838 |
| TN | random_forest | 50508 | 0.0874 | 0.9572 | 0.0618 |
| TN | xgboost | 50508 | 0.0878 | 0.9563 | 0.0467 |
| MH | climatology | 17568 | 0.1833 | 0.7288 | 0.0989 |
| MH | persistence | 17568 | 0.0457 | 0.9361 | 0.0114 |
| MH | logistic | 17568 | 0.1153 | 0.9424 | 0.1249 |
| MH | random_forest | 17568 | 0.0654 | 0.9716 | 0.0505 |
| MH | xgboost | 17568 | 0.0653 | 0.9706 | 0.0358 |
| KA | climatology | 6100 | 0.2131 | 0.6400 | 0.0853 |
| KA | persistence | 6100 | 0.0557 | 0.9292 | 0.0016 |
| KA | logistic | 6100 | 0.1212 | 0.9038 | 0.0531 |
| KA | random_forest | 6100 | 0.0840 | 0.9577 | 0.0579 |
| KA | xgboost | 6100 | 0.0816 | 0.9590 | 0.0399 |
### test

| Region | Model | n | Brier | ROC-AUC | ECE |
|---|---|---|---|---|---|
| TN | climatology | 25254 | 0.2690 | 0.6440 | 0.1824 |
| TN | persistence | 25254 | 0.0736 | 0.9213 | 0.0224 |
| TN | logistic | 25254 | 0.1225 | 0.9044 | 0.0191 |
| TN | random_forest | 25254 | 0.0879 | 0.9527 | 0.0350 |
| TN | xgboost | 25254 | 0.0922 | 0.9513 | 0.0356 |
| MH | climatology | 8784 | 0.1871 | 0.7340 | 0.0710 |
| MH | persistence | 8784 | 0.0649 | 0.9146 | 0.0107 |
| MH | logistic | 8784 | 0.0922 | 0.9531 | 0.0748 |
| MH | random_forest | 8784 | 0.0679 | 0.9729 | 0.0505 |
| MH | xgboost | 8784 | 0.0702 | 0.9701 | 0.0427 |
| KA | climatology | 3050 | 0.1971 | 0.7164 | 0.0526 |
| KA | persistence | 3050 | 0.0591 | 0.9293 | 0.0015 |
| KA | logistic | 3050 | 0.1193 | 0.9091 | 0.0481 |
| KA | random_forest | 3050 | 0.0865 | 0.9535 | 0.0418 |
| KA | xgboost | 3050 | 0.0854 | 0.9548 | 0.0388 |

## Target: `revival`

### val

| Region | Model | n | Brier | ROC-AUC | ECE |
|---|---|---|---|---|---|
| TN | climatology | 50508 | 0.0338 | 0.5256 | 0.0468 |
| TN | persistence | 50508 | 0.0297 | 0.5199 | 0.0005 |
| TN | logistic | 50508 | 0.0514 | 0.9848 | 0.0638 |
| TN | random_forest | 50508 | 0.0205 | 0.9951 | 0.0315 |
| TN | xgboost | 50508 | 0.0129 | 0.9968 | 0.0140 |
| MH | climatology | 17568 | 0.0270 | 0.5460 | 0.0394 |
| MH | persistence | 17568 | 0.0236 | 0.5163 | 0.0062 |
| MH | logistic | 17568 | 0.0567 | 0.9844 | 0.0725 |
| MH | random_forest | 17568 | 0.0160 | 0.9952 | 0.0262 |
| MH | xgboost | 17568 | 0.0104 | 0.9968 | 0.0104 |
| KA | climatology | 6100 | 0.0317 | 0.5071 | 0.0464 |
| KA | persistence | 6100 | 0.0277 | 0.5188 | 0.0017 |
| KA | logistic | 6100 | 0.0508 | 0.9801 | 0.0657 |
| KA | random_forest | 6100 | 0.0208 | 0.9936 | 0.0325 |
| KA | xgboost | 6100 | 0.0124 | 0.9963 | 0.0127 |
### test

| Region | Model | n | Brier | ROC-AUC | ECE |
|---|---|---|---|---|---|
| TN | climatology | 25254 | 0.0414 | 0.5217 | 0.0517 |
| TN | persistence | 25254 | 0.0374 | 0.5244 | 0.0090 |
| TN | logistic | 25254 | 0.0500 | 0.9839 | 0.0608 |
| TN | random_forest | 25254 | 0.0188 | 0.9962 | 0.0284 |
| TN | xgboost | 25254 | 0.0125 | 0.9974 | 0.0130 |
| MH | climatology | 8784 | 0.0374 | 0.5353 | 0.0460 |
| MH | persistence | 8784 | 0.0340 | 0.5225 | 0.0053 |
| MH | logistic | 8784 | 0.0463 | 0.9856 | 0.0596 |
| MH | random_forest | 8784 | 0.0161 | 0.9956 | 0.0245 |
| MH | xgboost | 8784 | 0.0104 | 0.9978 | 0.0106 |
| KA | climatology | 3050 | 0.0339 | 0.5230 | 0.0473 |
| KA | persistence | 3050 | 0.0308 | 0.5203 | 0.0017 |
| KA | logistic | 3050 | 0.0625 | 0.9766 | 0.0790 |
| KA | random_forest | 3050 | 0.0234 | 0.9941 | 0.0358 |
| KA | xgboost | 3050 | 0.0158 | 0.9951 | 0.0164 |

## Target: `dry_spell`

### val

| Region | Model | n | Brier | ROC-AUC | ECE |
|---|---|---|---|---|---|
| TN | climatology | 50508 | 0.1801 | 0.6416 | 0.0750 |
| TN | persistence | 50508 | 0.0381 | 0.9441 | 0.0048 |
| TN | logistic | 50508 | 0.1403 | 0.8978 | 0.1321 |
| TN | random_forest | 50508 | 0.0897 | 0.9501 | 0.0813 |
| TN | xgboost | 50508 | 0.0857 | 0.9507 | 0.0584 |
| MH | climatology | 17568 | 0.1119 | 0.7490 | 0.0790 |
| MH | persistence | 17568 | 0.0214 | 0.9486 | 0.0078 |
| MH | logistic | 17568 | 0.1173 | 0.9503 | 0.1561 |
| MH | random_forest | 17568 | 0.0616 | 0.9729 | 0.0785 |
| MH | xgboost | 17568 | 0.0613 | 0.9689 | 0.0607 |
| KA | climatology | 6100 | 0.1411 | 0.6223 | 0.0838 |
| KA | persistence | 6100 | 0.0292 | 0.9413 | 0.0021 |
| KA | logistic | 6100 | 0.0971 | 0.9245 | 0.0869 |
| KA | random_forest | 6100 | 0.0764 | 0.9486 | 0.0656 |
| KA | xgboost | 6100 | 0.0709 | 0.9494 | 0.0365 |
### test

| Region | Model | n | Brier | ROC-AUC | ECE |
|---|---|---|---|---|---|
| TN | climatology | 25254 | 0.2294 | 0.6512 | 0.1406 |
| TN | persistence | 25254 | 0.0496 | 0.9413 | 0.0146 |
| TN | logistic | 25254 | 0.1217 | 0.9164 | 0.0673 |
| TN | random_forest | 25254 | 0.0955 | 0.9482 | 0.0604 |
| TN | xgboost | 25254 | 0.1041 | 0.9399 | 0.0607 |
| MH | climatology | 8784 | 0.1088 | 0.7120 | 0.1033 |
| MH | persistence | 8784 | 0.0201 | 0.9418 | 0.0103 |
| MH | logistic | 8784 | 0.1031 | 0.9663 | 0.1426 |
| MH | random_forest | 8784 | 0.0704 | 0.9673 | 0.0979 |
| MH | xgboost | 8784 | 0.0668 | 0.9637 | 0.0785 |
| KA | climatology | 3050 | 0.1256 | 0.7101 | 0.0441 |
| KA | persistence | 3050 | 0.0267 | 0.9478 | 0.0041 |
| KA | logistic | 3050 | 0.0953 | 0.9237 | 0.0812 |
| KA | random_forest | 3050 | 0.0742 | 0.9531 | 0.0701 |
| KA | xgboost | 3050 | 0.0690 | 0.9520 | 0.0466 |

## Geography questions this table is meant to raise

1. Does a region consistently show worse Brier/calibration than the global mean → candidate geographic domain shift to test in Phase G ablation.
2. Break/dry-spell are high-frequency states and dominate Brier; onset/revival regional noise is expected.
