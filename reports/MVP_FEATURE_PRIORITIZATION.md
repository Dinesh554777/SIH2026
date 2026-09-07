# SIH26086 — MVP Feature Prioritization

Date: 2026-09-07 · Status: **DRAFT — prioritization for the 36-hour build; frozen model input lists are fixed by FREEZE_H.json.**

Context: the MVP may not need to rebuild the full 97-feature Phase H matrix at runtime for
every cell. It must only reproduce the exact inputs the frozen models consume.

---

## 1. What the frozen models actually need (fixed, non-optional)

| Model | Inputs | Count |
| ----- | ------ | ----- |
| Persistence (onset / break / dry-spell) | previous-day target state per cell + dseason; dseason==1 → cell-dseason climatology (train-fitted) | 2 (state, dseason) |
| XGBoost (revival) | Group B = 51 Group A + 13 `th_*` = 64 features | 64 |

Group B feature names come from `src/modeling/phase_h/modeling.group_features(ph, "B")`
and the artifact `models/phase_h/B/revival/CONFIG.json`. Imputation medians are the frozen
train medians for `th_rstd7`, `th_rstd14`, `sp_mean_lag1`.

**Rule:** the 64 features are the mandatory core. Everything else is optional UI enrichment.

---

## 2. Priority framework (Must / Should / Nice)

### MUST (required to be correct + defensible)
1. Feature pipeline reproduces the exact 64 Group-B features with the exact lag/rolling
   definitions from `src/labels/definitions.py` (windows 3/7/14/30; wet ≥1 mm; trace ≥2.5 mm).
2. Neighbour map for the 13 `sp_*`-style inputs that Group B needs (spatial aggregates use
   same-date neighbouring cells) — this is the subtle failure point.
3. Frozen imputation medians applied at inference (no refit).
4. Persistence transition init table (`p11`, `p01` per target above) + dseason climatology
   tables, all from train (2015–2021) only.
5. Provenance envelope in every response (freeze hash, periods, imputation note), since
   the judge/human must be able to audit "which model made this number?"
6. Cell registry (304 cells with lat/lon, canonical id, bbox region, "grid-cell-not-village" note).

### SHOULD (demonstrable value, low cost)
7. Probability cards with raw value + band + calibration ECE note (frozen values from FREEZE_H).
8. `observations_used` summary in the forecast payload (imd_rain_t, imd_sum7, th_accel) so
   "Why?" has substance.
9. `th_accel` and recent-window features surfaced in the explainability block (descriptive only).
10. Deterministic decision-rules table (the doc above) applied server-side — so the demo
    shows interpretation + suggested action, not just numbers.
11. A single ready-made demo date from the 2024 test period, pre-scripted, so the officer
    demo is reproducible offline.

### NICE (only if time remains)
12. LLM one-paragraph summary of the rule output (bounded, no probabilities).
13. Multi-cell band-count summary for a small region (no cross-cell averaging).
14. Minimal styling + colour bands on the dashboard.
15. Error/insufficient-data card behaviour.
16. Re-forecast convenience endpoint for the demo script.

---

## 3. Anti-priorities (explicitly excluded)

- Retraining or tuning ANY model (frozen contract).
- LSTM/GRU/Transformer/CNN or any new ML.
- Live IMD/CHIRPS ingest API integrations (demo uses research data + simulated "today").
- Authentication, persistence DB, user profiles.
- GIS village/block overlay (never implied).
- Mobile app.
- District-scale aggregation as a headline product (post-MVP).

---

## 4. Cost-to-value table (for 36-h scoping)

| Priority | Rough effort | Value |
| -------- | ------------ | ----- |
| 1–3 (features/imputation correctness) | Moderate (build + tests) | Gates everything |
| 4 (persistence init) | Low | Correct baseline cards |
| 5 (provenance) | Low | Judge defensibility |
| 6 (registry) | Low | Required anyway |
| 7–8 (cards + observations) | Low | Core UX |
| 9–10 (explain + rules) | Low–moderate | The "decision support" claim |
| 11 (demo script) | Low | Reproducibility |
| 12–16 (LLM, styling) | Variable | Polish only |