# SIH26086 — MVP Evaluator Review (self-assessment against likely judging criteria)

Date: 2026-09-07 · Verdict for the documentation phase: **APPROVE TO BUILD** (provisionally).
The 10 answers below are the ones a review panel would hold the team accountable for; each
is grounded in the freeze files and Phase H artifacts, not assertion.

---

## 1. Is the correct problem being solved?

**Yes — calibrated subseasonal regime awareness, not deterministic weather prediction.**
The MoES-informed problem is about onset/break/revival and dry spells at practical spatial
scales. Product spec targets an agriculture extension officer as the operating user; a
probabilistic state card + near-term guidance is exactly the decision aid absent today.
Deterministic claims are explicitly banned in UI/provenance copy.

## 2. Does the science/model satisfy the "hyperlocal" premise honestly?

**Honest claim: cell-scale (0.25°), not point/village.**
304 pilot cells (TN 207, MH 72, KA 25 region-mapped); every artifact carries
`admin_note: "grid_cell_only"`. No village/block overlay, no district-averaged headline.
This is the defensible version of "hyperlocal."

## 3. Does the AI submission actually use ML where it earns its keep?

**Yes, and honestly scoped.** Freeze report shows ML (XGBoost) **only** improves revival
(validation Brier 0.01226→0.00806; PR-AUC 0.906→0.949; ECE 0.013→0.008; 2024 test Brier
0.01230→0.00723, PR-AUC 0.939→0.972). For onset/break/dry-spell, persistence is better
calibrated and was kept. Claiming "AI everywhere" would have been dishonest; the submission
claims "ML where it works, facts where it doesn't."

## 4. Was the test/validation design leak-free?

**Yes.** Chronological splits (train 2015–2021 / val 2022–2023 / test 2024), no shuffle;
ONI guard (+45 d release buffer); 10 leakage tests in the suite; freeze note records
"2024 TEST DATA WAS NOT USED FOR FEATURE SELECTION OR MODEL SELECTION." All imputation
medians train-only and frozen. The demo pivot dates are 2024.

## 5. Is the solution usable by the stated user?

**Designed so.** 8-step journey (select → grid → observe → model → band → advisory →
why → provenance). Cards use raw % + a band; "Why?" lists real features (th_accel, 7-day
sum, wet streaks) with a descriptive caveat; agronomic actions flagged expert-validation-needed.

## 6. Uncertainty handling — is it genuine?

**Yes, three layers.** (a) Raw calibrated probabilities displayed (never rounded to a
certainty). (b) Communication bands with a documented "aids, not guarantees" note. (c)
Calibration quality surfaced (ECE per target from FREEZE_H). Missing-data path refuses to
emit a number (409/insufficient-data card) instead of faking one.

## 7. Is the agricultural advisory safety-barred?

**Yes.** Every suggested action carries `expert_validation: "requires expert validation"`;
rules table is marked draft-until-extension-review; LLM cannot produce probabilities or
thresholds; deterministic language is banned. The product positions the officer (not the
LLM) as the final decision-maker.

## 8. Is the LLM used responsibly / bounded?

**LLM is optional and bounded by design.** It may only rephrase rule-table output and the
"why" (descriptive, non-causal). It must not forecast, must not set thresholds, must not
claim causation. Fail-fast validation is part of the rules doc.

## 9. Is reproducibility from the repo achievable?

**Yes.** Frozen artifacts + FREEZE_H.json + the two parquet files + the API contract define
a reproducible envelope; the demo scenario document pins exact pivot numbers; a regression
test pins demo-cell revival probability = 0.6047 on 2024-08-12. Build is
`pytest`-gated at each 36-h milestone.

## 10. What is the one-line strongest claim, and what are the honest limits?

Strong claim: *"Calibrated, leak-free probabilities for four monsoon regimes at 0.25°,
with ML only where validated (revival), served to an extension officer with bounded,
uncertainty-first advisory language."*

Honest limits: (a) regime horizons are nowcast-state, not multi-day deterministic;
(b) cells ≠ villages; (c) agronomic rules await extension validation; (d) pilot covers
TN/MH/KA 304 cells; (e) persistence is deliberately retained for 3 of 4 targets.

---

## Overall verdict

| Criterion | Grade |
| --------- | ----- |
| Problem fit | A |
| Model honesty | A |
| Leakage hygiene | A |
| Uncertainty practice | A |
| Governance / safety copy | B+ (rules need expert sign-off) |
| Reproducibility | A |

**Decision: PROCEED to implementation (hours 0–36) once the human approves this doc set.**
Everything is documentation at this phase; no frontend/backend exists yet, by design.