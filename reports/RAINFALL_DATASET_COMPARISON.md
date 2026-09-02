# RAINFALL_DATASET_COMPARISON (IMD 0.25 vs CHIRPS v3.0 0.05 -> IMD grid)

Metrics over pilot bbox (lat 9.8-20.7N, lon 72.4-81.1E). Wet-day = >=1 mm. A=IMD, B=CHIRPS. bias = mean(B-A). Days = CHIRPS days matched that year.

NOTE: rows/progress limited to years where CHIRPS pilot extraction has completed.

| period | days | corr | MAE | RMSE | bias | wet A% | wet B% | p95 A | p95 B | p99 A | p99 B | JJAS A | JJAS B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2015 | 365 | 0.476 | 3.54 | 10.10 | +0.176 | 22.24 | 30.02 | 17.2 | 16.7 | 47.7 | 41.3 | 5.65 | 4.83 |
| 2016 | 366 | 0.501 | 3.39 | 10.89 | +0.223 | 19.93 | 26.75 | 17.3 | 17.2 | 53.6 | 46.1 | 7.45 | 6.11 |
| 2015-2024 (available) | 731 | 0.489 | 3.47 | 10.50 | +0.199 | 21.08 | 28.38 | 17.3 | 16.9 | 50.6 | 43.9 | - | - |
