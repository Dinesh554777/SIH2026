# PHASE H — GENERALIZATION REPORT (VALIDATION 2022–2023)

Date: 2026-09-07

Only the one candidate that beat the frozen reference on aggregate validation is
generalized deep: **revival, XGBoost + temporal (Group B)**. For onset/break/dry_spell no
candidate beat the frozen reference, so no candidate is carried forward.

## Revival candidate (B / xgboost) — year-by-year

| Year | Cand Brier | Frozen Brier | Cand PR-AUC | Cand ECE | Cand Recall | Cand Precision | Cand n_pos |
| ---- | ---------: | -----------: | ----------: | -------: | ----------: | --------------: | ---------: |
| 2022 | 0.007087 | 0.011430 | 0.963 | 0.0076 | 0.970 | 0.759 | 1,073 |
| 2023 | 0.009040 | 0.013088 | 0.931 | 0.0091 | 0.954 | 0.721 | 1,076 |

The improvement holds in **both** years. Not a single-year artifact.

## Revival candidate — region-by-region (2022+2023 pooled)

| Region | Cand Brier | Frozen Brier | Cand PR-AUC | Cand ECE | n_pos |
| ------ | ---------: | -----------: | ----------: | -------: | ----: |
| Tamil Nadu (TN)  | 0.008377 | 0.012903 | 0.954 | 0.0090 | 1,551 |
| Maharashtra (MH) | 0.006979 | 0.010358 | 0.933 | 0.0065 | 424 |
| Karnataka (KA)   | 0.008584 | 0.012396 | 0.939 | 0.0089 | 174 |

The improvement is **geographically stable** across all three regions, including when
pooled. Even KA (174 positives) shows the improvement, so it is not driven by a single
dense region. Regions derive from bbox grouping only (admin not authoritative).

## Rare-event read (H7.1)

- Revival has enough positives (n≈2,149 pooled val; 1,073 + 1,076 by year; ≥174 per region)
  to trust PR-AUC/calibration. Brier 0.00806, PR-AUC 0.949, ECE 0.008 on validation.
- Onset is the rarest (592 pos in val). ML approaches persistence's Brier but never beats
  it; the frozen persistence baseline remains preferable and is not overinterpreted.

## Stability verdict

The revival improvement is **consistent across years, consistent across regions,
calibration-driven and discrimination-driven** (higher PR-AUC, lower ECE), with healthy
event counts. It is not a one-year or one-region fluke and not driven by a handful of events.
