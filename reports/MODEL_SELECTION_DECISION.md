# MODEL SELECTION DECISION

Generated 2026-09-06T14:02:17Z — selection computed on **VALIDATION (2022-2023) only**; 2024 was not opened before this file was written (`data/processed/FREEZE.json`).

## Frozen rule

Per target: winner = learned model (logistic/RF/XGB) that improves validation Brier over **both** climatology and persistence by ≥ 0.001 and has defined ROC-AUC; tie-break = lowest validation ECE then lowest Brier. If none qualify, the better baseline wins.

## Winners

### onset
- Frozen winner: **persistence** (baseline)
- Validation Brier climatology / persistence: 0.00906 / 0.00792

### break
- Frozen winner: **persistence** (baseline)
- Validation Brier climatology / persistence: 0.21135 / 0.05566

### revival
- Frozen winner: **xgboost** (learned)
- Validation Brier climatology / persistence: 0.03203 / 0.0281

### dry_spell
- Frozen winner: **persistence** (baseline)
- Validation Brier climatology / persistence: 0.16076 / 0.0334


## Answers to the 10 required questions

- **1. Which model performed best?** Per-target winners selected on validation evidence (table below).
- **2. For which target?** onset: persistence; break: persistence; revival: xgboost; dry_spell: persistence
- **3. Did it beat climatology?** onset: no; break: no; revival: yes; dry_spell: no
- **4. Did it beat persistence?** Same as 3.
- **5. Was it calibrated?** Per-model ECE and reliability in PROBABILISTIC_EVALUATION_REPORT.md; the winning model's calibration is part of the selection tie-break.
- **6. Performance stable across years?** Only 3 evaluation seasons; see YEARLY_GENERALIZATION_REPORT.md.
- **7. Performance stable across regions?** See REGIONAL_PERFORMANCE_REPORT.md (KA small n).
- **8. Additional complexity?** Trees > logistic > baselines; accepted only with material Brier gain.
- **9. Scientifically meaningful?** Requires ΔBrier ≥ 0.001 vs both baselines on validation; the decision wind checks test consistency but selection never used test.
- **10. Proceed to Phase G?** Only if learned models deliver material, repeatable probabilistic gains; per-target it is acceptable to freeze different models (or a baseline).

## Validation metric detail

   target         model    brier  roc_auc   pr_auc       f1      ece
    break   climatology 0.211346 0.671664 0.445028 0.419445 0.086455
    break      logistic 0.132350 0.903378 0.807888 0.736616 0.090598
    break   persistence 0.055656 0.931686 0.854427 0.907452 0.001828
    break random_forest 0.081901 0.960954 0.921836 0.823487 0.057801
    break       xgboost 0.081956 0.960298 0.922722 0.825704 0.043218
dry_spell   climatology 0.160762 0.660841 0.294358 0.165506 0.072850
dry_spell      logistic 0.131315 0.909614 0.721444 0.634969 0.133824
dry_spell   persistence 0.033396 0.945373 0.852281 0.913286 0.001793
dry_spell random_forest 0.081970 0.955499 0.862064 0.740878 0.079323
dry_spell       xgboost 0.078700 0.955069 0.862601 0.744220 0.056551
    onset   climatology 0.009060 0.547531 0.012371 0.009868 0.013736
    onset      logistic 0.073457 0.971880 0.192650 0.129127 0.116680
    onset   persistence 0.007916 0.508154 0.008112 0.000000 0.000066
    onset random_forest 0.019722 0.990268 0.452899 0.337327 0.033802
    onset       xgboost 0.009408 0.992296 0.532866 0.493136 0.010387
  revival   climatology 0.032029 0.528439 0.030961 0.000000 0.044999
  revival      logistic 0.052631 0.984113 0.597961 0.443124 0.065988
  revival   persistence 0.028102 0.518986 0.030081 0.000000 0.001246
  revival random_forest 0.019488 0.994962 0.841529 0.683963 0.030299
  revival       xgboost 0.012259 0.996781 0.906315 0.770362 0.013025
