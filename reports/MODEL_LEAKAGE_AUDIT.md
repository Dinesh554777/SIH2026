# MODEL LEAKAGE AUDIT — SIH26086 (Phase D)

Generated 2026-09-06 · matrix: `data/processed/training_matrix.parquet`

| check | result | detail |
| --- | --- | --- |
| check_l1 | PASS | imd_sum7 recomputed from <=T slice for 40 samples (future +1d value: changed? no (feature equal)) |
| check_l2 | PASS | chirps_sum7 recomputed from <=T slice for 40 samples |
| check_l3 | PASS | nasa window is trailing-7 incl.-T (min_periods=1 rolling mean); sampling bounded |
| check_l4 | PASS | oni_1 always the latest >=45-d-released season (60 samples) |
| check_l5 | PASS | all LAG windows right-anchored inclusive-T (imd_sum3 == rain[t-2..t]) |
| check_l6 | PASS | climatology column identical train-only vs full; anomalies match train-only clim |
| check_l7 | PASS | labels for 1 sampled cell recomputed from its OWN series only -> match matrix |
| check_l8 | PASS | duplicate (cell_id,date) rows = 0 |
| check_l9 | PASS | unique spatial cells = 304 |
| check_l10 | PASS | split identical to calendar rule for all 370880 rows |
