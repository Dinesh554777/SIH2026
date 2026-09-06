# YEARLY GENERALIZATION REPORT (Phases E-F)

Generated 2026-09-06T14:02:17Z

## CRITICAL limitation — only 3 evaluation seasons

Only **3** independent evaluation seasons exist (2022, 2023, 2024). Each season has ~37,000 daily rows, but days within a season and neighboring grid cells are strongly correlated — a large row count is **not** evidence of many independent samples. Do not interpret single-year values or the 3-season average as robust generalization. Model variance across years is the honest estimate of instability.

## Target: `onset`

### climatology
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0089` · best `0.0086` · worst `0.0091` · std `0.0002`
- Brier by year: 2022: 0.00913, 2023: 0.00899, 2024: 0.00859

### persistence
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0080` · best `0.0077` · worst `0.0081` · std `0.0002`
- Brier by year: 2022: 0.0081, 2023: 0.00773, 2024: 0.00802

### logistic
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0673` · best `0.0549` · worst `0.0799` · std `0.0102`
- Brier by year: 2022: 0.06704, 2023: 0.07987, 2024: 0.05493

### random_forest
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0192` · best `0.0182` · worst `0.0199` · std `0.0007`
- Brier by year: 2022: 0.01957, 2023: 0.01987, 2024: 0.01816

### xgboost
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0088` · best `0.0074` · worst `0.0098` · std `0.0010`
- Brier by year: 2022: 0.00903, 2023: 0.00979, 2024: 0.00745


## Target: `break`

### climatology
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.2221` · best `0.2053` · worst `0.2437` · std `0.0160`
- Brier by year: 2022: 0.21735, 2023: 0.20535, 2024: 0.24369

### persistence
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0605` · best `0.0548` · worst `0.0703` · std `0.0070`
- Brier by year: 2022: 0.05654, 2023: 0.05477, 2024: 0.07032

### logistic
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.1266` · best `0.1132` · worst `0.1515` · std `0.0176`
- Brier by year: 2022: 0.11323, 2023: 0.15146, 2024: 0.11508

### random_forest
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0823` · best `0.0711` · worst `0.0927` · std `0.0089`
- Brier by year: 2022: 0.07107, 2023: 0.09273, 2024: 0.08305

### xgboost
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0835` · best `0.0763` · worst `0.0876` · std `0.0051`
- Brier by year: 2022: 0.07632, 2023: 0.0876, 2024: 0.08645


## Target: `revival`

### climatology
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0346` · best `0.0318` · worst `0.0399` · std `0.0037`
- Brier by year: 2022: 0.03228, 2023: 0.03178, 2024: 0.03987

### persistence
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0307` · best `0.0281` · worst `0.0360` · std `0.0037`
- Brier by year: 2022: 0.02806, 2023: 0.02814, 2024: 0.03604

### logistic
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0518` · best `0.0490` · worst `0.0562` · std `0.0032`
- Brier by year: 2022: 0.04903, 2023: 0.05623, 2024: 0.05013

### random_forest
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0192` · best `0.0169` · worst `0.0220` · std `0.0021`
- Brier by year: 2022: 0.01693, 2023: 0.02205, 2024: 0.0185

### xgboost
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0123` · best `0.0114` · worst `0.0131` · std `0.0007`
- Brier by year: 2022: 0.01143, 2023: 0.01309, 2024: 0.0123


## Target: `dry_spell`

### climatology
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.1713` · best `0.1495` · worst `0.1923` · std `0.0175`
- Brier by year: 2022: 0.17198, 2023: 0.14954, 2024: 0.19229

### persistence
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0358` · best `0.0314` · worst `0.0407` · std `0.0038`
- Brier by year: 2022: 0.03544, 2023: 0.03135, 2024: 0.04074

### logistic
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.1259` · best `0.1100` · worst `0.1527` · std `0.0190`
- Brier by year: 2022: 0.10997, 2023: 0.15266, 2024: 0.11514

### random_forest
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0839` · best `0.0692` · worst `0.0947` · std `0.0108`
- Brier by year: 2022: 0.06921, 2023: 0.09473, 2024: 0.08779

### xgboost
- Seasons evaluated: 3 (2022, 2023, 2024).
- Avg yearly Brier `0.0832` · best `0.0704` · worst `0.0923` · std `0.0093`
- Brier by year: 2022: 0.07045, 2023: 0.08695, 2024: 0.09235


## Figure

- `reports/figures/yearly_brier.png` — Brier by calendar year 2015–2024 (train years 2015-2021 illustrative only; operational evidence = 2022–2024).
