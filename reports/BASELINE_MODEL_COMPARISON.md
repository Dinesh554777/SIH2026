# BASELINE MODEL COMPARISON (Phases E-F)

Generated 2026-09-06T14:02:17Z · random seed 42

## Answering `Did machine learning add value?`

## Target: `onset`

| Model | Split | Brier | LogLoss | ROC-AUC | PR-AUC | P | R | F1 | ECE |
|---|---|---|---|---|---|---|---|---|---|
| climatology | val | 0.0091 | 0.1996 | 0.5475 | 0.0124 | 0.1875 | 0.0051 | 0.0099 | 0.0137 |
| climatology | test | 0.0086 | 0.1743 | 0.6144 | 0.0437 | 0.7500 | 0.0200 | 0.0390 | 0.0118 |
| persistence | val | 0.0079 | 0.0464 | 0.5082 | 0.0081 | 0.0000 | 0.0000 | 0.0000 | 0.0001 |
| persistence | test | 0.0080 | 0.0469 | 0.5082 | 0.0082 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| logistic | val | 0.0735 | 0.2381 | 0.9719 | 0.1926 | 0.0692 | 0.9645 | 0.1291 | 0.1167 |
| logistic | test | 0.0549 | 0.1871 | 0.9813 | 0.2451 | 0.0955 | 0.9733 | 0.1740 | 0.0856 |
| random_forest | val | 0.0197 | 0.0624 | 0.9903 | 0.4529 | 0.2062 | 0.9274 | 0.3373 | 0.0338 |
| random_forest | test | 0.0182 | 0.0578 | 0.9930 | 0.5688 | 0.2321 | 0.9500 | 0.3730 | 0.0327 |
| xgboost | val | 0.0094 | 0.0302 | 0.9923 | 0.5329 | 0.3587 | 0.7889 | 0.4931 | 0.0104 |
| xgboost | test | 0.0074 | 0.0241 | 0.9949 | 0.6017 | 0.4207 | 0.7867 | 0.5482 | 0.0077 |

### Improvement over baselines (ΔBrier = baseline − model; positive = improvement; ΔROC-AUC = model − baseline; higher better)

- **logistic vs climatology** (val): ΔBrier = `-0.0644` (Brier lower better → positive = improvement), relative = `-710.8%`, ΔROC-AUC = `0.4243`.
- **random_forest vs climatology** (val): ΔBrier = `-0.0107` (Brier lower better → positive = improvement), relative = `-117.7%`, ΔROC-AUC = `0.4427`.
- **xgboost vs climatology** (val): ΔBrier = `-0.0003` (Brier lower better → positive = improvement), relative = `-3.8%`, ΔROC-AUC = `0.4448`.
- **logistic vs persistence** (val): ΔBrier = `-0.0655` (Brier lower better → positive = improvement), relative = `-827.9%`, ΔROC-AUC = `0.4637`.
- **random_forest vs persistence** (val): ΔBrier = `-0.0118` (Brier lower better → positive = improvement), relative = `-149.1%`, ΔROC-AUC = `0.4821`.
- **xgboost vs persistence** (val): ΔBrier = `-0.0015` (Brier lower better → positive = improvement), relative = `-18.8%`, ΔROC-AUC = `0.4841`.

- **logistic vs climatology** (test): ΔBrier = `-0.0463` (Brier lower better → positive = improvement), relative = `-539.8%`, ΔROC-AUC = `0.3670`.
- **random_forest vs climatology** (test): ΔBrier = `-0.0096` (Brier lower better → positive = improvement), relative = `-111.5%`, ΔROC-AUC = `0.3786`.
- **xgboost vs climatology** (test): ΔBrier = `+0.0011` (Brier lower better → positive = improvement), relative = `+13.3%`, ΔROC-AUC = `0.3805`.
- **logistic vs persistence** (test): ΔBrier = `-0.0469` (Brier lower better → positive = improvement), relative = `-584.7%`, ΔROC-AUC = `0.4731`.
- **random_forest vs persistence** (test): ΔBrier = `-0.0101` (Brier lower better → positive = improvement), relative = `-126.4%`, ΔROC-AUC = `0.4848`.
- **xgboost vs persistence** (test): ΔBrier = `+0.0006` (Brier lower better → positive = improvement), relative = `+7.2%`, ΔROC-AUC = `0.4867`.

## Target: `break`

| Model | Split | Brier | LogLoss | ROC-AUC | PR-AUC | P | R | F1 | ECE |
|---|---|---|---|---|---|---|---|---|---|
| climatology | val | 0.2113 | 1.0642 | 0.6717 | 0.4450 | 0.4861 | 0.3689 | 0.4194 | 0.0865 |
| climatology | test | 0.2437 | 1.2939 | 0.6660 | 0.5386 | 0.5689 | 0.3259 | 0.4144 | 0.1352 |
| persistence | val | 0.0557 | 0.2220 | 0.9317 | 0.8544 | 0.9099 | 0.9050 | 0.9075 | 0.0018 |
| persistence | test | 0.0703 | 0.2700 | 0.9229 | 0.8691 | 0.9123 | 0.9100 | 0.9112 | 0.0136 |
| logistic | val | 0.1323 | 0.3929 | 0.9034 | 0.8079 | 0.6381 | 0.8711 | 0.7366 | 0.0906 |
| logistic | test | 0.1151 | 0.3504 | 0.9157 | 0.8679 | 0.7604 | 0.8834 | 0.8173 | 0.0165 |
| random_forest | val | 0.0819 | 0.2541 | 0.9610 | 0.9218 | 0.7561 | 0.9040 | 0.8235 | 0.0578 |
| random_forest | test | 0.0830 | 0.2583 | 0.9584 | 0.9424 | 0.8127 | 0.9295 | 0.8672 | 0.0351 |
| xgboost | val | 0.0820 | 0.2474 | 0.9603 | 0.9227 | 0.7675 | 0.8934 | 0.8257 | 0.0432 |
| xgboost | test | 0.0864 | 0.2585 | 0.9575 | 0.9437 | 0.8076 | 0.9209 | 0.8606 | 0.0351 |

### Improvement over baselines (ΔBrier = baseline − model; positive = improvement; ΔROC-AUC = model − baseline; higher better)

- **logistic vs climatology** (val): ΔBrier = `+0.0790` (Brier lower better → positive = improvement), relative = `+37.4%`, ΔROC-AUC = `0.2317`.
- **random_forest vs climatology** (val): ΔBrier = `+0.1294` (Brier lower better → positive = improvement), relative = `+61.2%`, ΔROC-AUC = `0.2893`.
- **xgboost vs climatology** (val): ΔBrier = `+0.1294` (Brier lower better → positive = improvement), relative = `+61.2%`, ΔROC-AUC = `0.2886`.
- **logistic vs persistence** (val): ΔBrier = `-0.0767` (Brier lower better → positive = improvement), relative = `-137.8%`, ΔROC-AUC = `-0.0283`.
- **random_forest vs persistence** (val): ΔBrier = `-0.0262` (Brier lower better → positive = improvement), relative = `-47.2%`, ΔROC-AUC = `0.0293`.
- **xgboost vs persistence** (val): ΔBrier = `-0.0263` (Brier lower better → positive = improvement), relative = `-47.3%`, ΔROC-AUC = `0.0286`.

- **logistic vs climatology** (test): ΔBrier = `+0.1286` (Brier lower better → positive = improvement), relative = `+52.8%`, ΔROC-AUC = `0.2496`.
- **random_forest vs climatology** (test): ΔBrier = `+0.1606` (Brier lower better → positive = improvement), relative = `+65.9%`, ΔROC-AUC = `0.2923`.
- **xgboost vs climatology** (test): ΔBrier = `+0.1572` (Brier lower better → positive = improvement), relative = `+64.5%`, ΔROC-AUC = `0.2914`.
- **logistic vs persistence** (test): ΔBrier = `-0.0448` (Brier lower better → positive = improvement), relative = `-63.6%`, ΔROC-AUC = `-0.0072`.
- **random_forest vs persistence** (test): ΔBrier = `-0.0127` (Brier lower better → positive = improvement), relative = `-18.1%`, ΔROC-AUC = `0.0354`.
- **xgboost vs persistence** (test): ΔBrier = `-0.0161` (Brier lower better → positive = improvement), relative = `-22.9%`, ΔROC-AUC = `0.0346`.

## Target: `revival`

| Model | Split | Brier | LogLoss | ROC-AUC | PR-AUC | P | R | F1 | ECE |
|---|---|---|---|---|---|---|---|---|---|
| climatology | val | 0.0320 | 0.6502 | 0.5284 | 0.0310 | 0.0000 | 0.0000 | 0.0000 | 0.0450 |
| climatology | test | 0.0399 | 0.8385 | 0.5250 | 0.0399 | 0.0000 | 0.0000 | 0.0000 | 0.0499 |
| persistence | val | 0.0281 | 0.1301 | 0.5190 | 0.0301 | 0.0000 | 0.0000 | 0.0000 | 0.0012 |
| persistence | test | 0.0360 | 0.1589 | 0.5236 | 0.0392 | 0.0000 | 0.0000 | 0.0000 | 0.0075 |
| logistic | val | 0.0526 | 0.1637 | 0.9841 | 0.5980 | 0.2855 | 0.9888 | 0.4431 | 0.0660 |
| logistic | test | 0.0501 | 0.1555 | 0.9839 | 0.6644 | 0.3530 | 0.9849 | 0.5198 | 0.0620 |
| random_forest | val | 0.0195 | 0.0647 | 0.9950 | 0.8415 | 0.5249 | 0.9814 | 0.6840 | 0.0303 |
| random_forest | test | 0.0185 | 0.0621 | 0.9959 | 0.9000 | 0.5984 | 0.9806 | 0.7432 | 0.0281 |
| xgboost | val | 0.0123 | 0.0406 | 0.9968 | 0.9063 | 0.6475 | 0.9507 | 0.7704 | 0.0130 |
| xgboost | test | 0.0123 | 0.0399 | 0.9973 | 0.9392 | 0.7024 | 0.9618 | 0.8119 | 0.0127 |

### Improvement over baselines (ΔBrier = baseline − model; positive = improvement; ΔROC-AUC = model − baseline; higher better)

- **logistic vs climatology** (val): ΔBrier = `-0.0206` (Brier lower better → positive = improvement), relative = `-64.3%`, ΔROC-AUC = `0.4557`.
- **random_forest vs climatology** (val): ΔBrier = `+0.0125` (Brier lower better → positive = improvement), relative = `+39.2%`, ΔROC-AUC = `0.4665`.
- **xgboost vs climatology** (val): ΔBrier = `+0.0198` (Brier lower better → positive = improvement), relative = `+61.7%`, ΔROC-AUC = `0.4683`.
- **logistic vs persistence** (val): ΔBrier = `-0.0245` (Brier lower better → positive = improvement), relative = `-87.3%`, ΔROC-AUC = `0.4651`.
- **random_forest vs persistence** (val): ΔBrier = `+0.0086` (Brier lower better → positive = improvement), relative = `+30.7%`, ΔROC-AUC = `0.4760`.
- **xgboost vs persistence** (val): ΔBrier = `+0.0158` (Brier lower better → positive = improvement), relative = `+56.4%`, ΔROC-AUC = `0.4778`.

- **logistic vs climatology** (test): ΔBrier = `-0.0103` (Brier lower better → positive = improvement), relative = `-25.7%`, ΔROC-AUC = `0.4589`.
- **random_forest vs climatology** (test): ΔBrier = `+0.0214` (Brier lower better → positive = improvement), relative = `+53.6%`, ΔROC-AUC = `0.4709`.
- **xgboost vs climatology** (test): ΔBrier = `+0.0276` (Brier lower better → positive = improvement), relative = `+69.2%`, ΔROC-AUC = `0.4723`.
- **logistic vs persistence** (test): ΔBrier = `-0.0141` (Brier lower better → positive = improvement), relative = `-39.1%`, ΔROC-AUC = `0.4603`.
- **random_forest vs persistence** (test): ΔBrier = `+0.0175` (Brier lower better → positive = improvement), relative = `+48.7%`, ΔROC-AUC = `0.4723`.
- **xgboost vs persistence** (test): ΔBrier = `+0.0237` (Brier lower better → positive = improvement), relative = `+65.9%`, ΔROC-AUC = `0.4737`.

## Target: `dry_spell`

| Model | Split | Brier | LogLoss | ROC-AUC | PR-AUC | P | R | F1 | ECE |
|---|---|---|---|---|---|---|---|---|---|
| climatology | val | 0.1608 | 1.1469 | 0.6608 | 0.2944 | 0.3852 | 0.1054 | 0.1655 | 0.0728 |
| climatology | test | 0.1923 | 1.3481 | 0.6630 | 0.3619 | 0.4241 | 0.0895 | 0.1478 | 0.1005 |
| persistence | val | 0.0334 | 0.1450 | 0.9454 | 0.8523 | 0.9151 | 0.9115 | 0.9133 | 0.0018 |
| persistence | test | 0.0407 | 0.1730 | 0.9449 | 0.8654 | 0.9191 | 0.9178 | 0.9184 | 0.0071 |
| logistic | val | 0.1313 | 0.3784 | 0.9096 | 0.7214 | 0.4992 | 0.8721 | 0.6350 | 0.1338 |
| logistic | test | 0.1151 | 0.3365 | 0.9245 | 0.7889 | 0.6114 | 0.9003 | 0.7282 | 0.0857 |
| random_forest | val | 0.0820 | 0.2478 | 0.9555 | 0.8621 | 0.6448 | 0.8706 | 0.7409 | 0.0793 |
| random_forest | test | 0.0878 | 0.2626 | 0.9540 | 0.8868 | 0.6838 | 0.8969 | 0.7760 | 0.0689 |
| xgboost | val | 0.0787 | 0.2362 | 0.9551 | 0.8626 | 0.6672 | 0.8413 | 0.7442 | 0.0566 |
| xgboost | test | 0.0923 | 0.2714 | 0.9488 | 0.8800 | 0.6823 | 0.8678 | 0.7640 | 0.0619 |

### Improvement over baselines (ΔBrier = baseline − model; positive = improvement; ΔROC-AUC = model − baseline; higher better)

- **logistic vs climatology** (val): ΔBrier = `+0.0294` (Brier lower better → positive = improvement), relative = `+18.3%`, ΔROC-AUC = `0.2488`.
- **random_forest vs climatology** (val): ΔBrier = `+0.0788` (Brier lower better → positive = improvement), relative = `+49.0%`, ΔROC-AUC = `0.2947`.
- **xgboost vs climatology** (val): ΔBrier = `+0.0821` (Brier lower better → positive = improvement), relative = `+51.0%`, ΔROC-AUC = `0.2942`.
- **logistic vs persistence** (val): ΔBrier = `-0.0979` (Brier lower better → positive = improvement), relative = `-293.2%`, ΔROC-AUC = `-0.0358`.
- **random_forest vs persistence** (val): ΔBrier = `-0.0486` (Brier lower better → positive = improvement), relative = `-145.5%`, ΔROC-AUC = `0.0101`.
- **xgboost vs persistence** (val): ΔBrier = `-0.0453` (Brier lower better → positive = improvement), relative = `-135.7%`, ΔROC-AUC = `0.0097`.

- **logistic vs climatology** (test): ΔBrier = `+0.0771` (Brier lower better → positive = improvement), relative = `+40.1%`, ΔROC-AUC = `0.2615`.
- **random_forest vs climatology** (test): ΔBrier = `+0.1045` (Brier lower better → positive = improvement), relative = `+54.3%`, ΔROC-AUC = `0.2910`.
- **xgboost vs climatology** (test): ΔBrier = `+0.0999` (Brier lower better → positive = improvement), relative = `+52.0%`, ΔROC-AUC = `0.2857`.
- **logistic vs persistence** (test): ΔBrier = `-0.0744` (Brier lower better → positive = improvement), relative = `-182.6%`, ΔROC-AUC = `-0.0203`.
- **random_forest vs persistence** (test): ΔBrier = `-0.0470` (Brier lower better → positive = improvement), relative = `-115.5%`, ΔROC-AUC = `0.0092`.
- **xgboost vs persistence** (test): ΔBrier = `-0.0516` (Brier lower better → positive = improvement), relative = `-126.7%`, ΔROC-AUC = `0.0039`.

## Frozen winners (VALIDATION only)

| Target | Winner | Kind |
|---|---|---|
| onset | persistence | baseline |
| break | persistence | baseline |
| revival | xgboost | learned |
| dry_spell | persistence | baseline |

*Calibration, decision logic and caveats: PROBABILISTIC_EVALUATION_REPORT.md, MODEL_SELECTION_DECISION.md.*
