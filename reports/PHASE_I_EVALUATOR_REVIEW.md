# Phase I Evaluator Review (SIH Judge)

**Reviewer:** SIH judge persona — 10 criteria · **Evidence:** run artifacts from
`python -m pytest tests/ -q` (68 passed), `python -m src.serving.demo`, live API
probes, and the Phase I reports + contract docs.

## 1. Is the correct problem being solved? — PASS

Yes, and honestly scoped: "given today's observed rainfall, what is the calibrated
probability that onset / break / revival / dry-spell is active **at pilot-grid-cell
resolution**". The product says grid cell, never village/block. It solves the
decision-support framing, not a claim-heavy pre-monsoon prediction.

## 2. Does the science/model satisfy "hyperlocal" honestly? — PASS

0.25° pilot grid (304 cells, TN/MH/KA) with cell-dannual climatology + cell-local
persistence + a frozen cell-agnostic XGB over 64 features including neighbouring-
cell aggregates. The region attribution is explicitly a heuristic bbox and the UI
labels the spatial unit as a grid cell, not a predicted administrative unit.

## 3. Does the AI actually use ML where it earns its keep? — PASS

Revival (the only target where deep non-sparse signal exists) uses a frozen
XGBoost classifier; onset/break/dry-spell keep frozen persistence because Phase G/H
showed ML variants could NOT beat it on validation (documented in FREEZE_H.json per
target). That is a defensible scientific choice, not a cop-out: the demo shows the
ML card is the *discriminating* signal on the revival day (0.60 vs persistence 0.03).

## 4. Was the test/validation design leak-free? — PASS

Train 2015–2021 · validation 2022–2023 · test 2024, all frozen. Imputation statistics,
climatologies, and persistence transitions are train-only by assertion in the test
suite; feature selection and model selection predate the 2024 pass; `FREEZE_H.json`
records "2024 TEST DATA WAS NOT USED". Static guards forbid `fit()`-style calls in
inference files.

## 5. Is the solution usable by the stated user? — PASS (MVP)

One page, four cards, band legend, current signal, guidance phrases, "why this
probability", model provenance, demo buttons. Works offline from `uvicorn`. The
"any village/district" expectation is correctly NOT attempted (grid cell language).

## 6. Uncertainty handling — genuine? — PASS

Calibrated probabilities with explicit band thresholds, validation ECE/Brier shown,
per-target probabilities, sensitivity deltas + training-median reference, and a
visible distinction between a probability and a claim. No point estimates posing as
certainty; every payload carries a horizon note ("after same-day observations").

## 7. Is the agricultural advisory safety-barred? — PASS

Deterministic, versioned rules map (band → interpretation → suggested action) with
the approved disclaimers; every response is framed as decision support, not
agronomic guarantees. No invented "farm facts", no fatal-action directives.

## 8. Is the LLM used responsibly / bounded? — PASS (by construction)

There is no LLM in the pipeline (static guard). If one is added later it may only
rephrase the deterministic table output; it cannot compute, modify, or invent any
number.

## 9. Is reproducibility from the repo achievable? — PASS

`pytest tests/ -q` → 68 green; demo asserts exact reproduction of the frozen 2024
value (revival 0.6047 on 2024-08-12) and parity of persistence vs the frozen
parquet references. Single run command. No hidden config, no secrets.

## 10. One-line strongest claim + honest limits

**Strongest:** "A frozen, leak-free, per-cell probabilistic engine over 304 pilot
grid cells that reproduces the textbook 2024 false-onset → dry-spell → revival
sequence (revival P 0.60→0.99) with fully disclosed provenance and no hardcoded
numbers."

**Honest limits:** 0.25° grid cells ≠ villages/blocks; 2024 never touched the
models; stack is a demo-grade single-service app (no auth/cloud/notifications);
explain is descriptive sensitivity, not causation; persistence cards can dominate
on break/dry-spell days by design.

---

## Evaluator Verdict

**PASS for the MVP demo.** The system is small, honest, real-inference, leak-free,
reproducible, safety-barred, and demonstrable in the required 60-second window.
No blocking defects found in the reviewed surface.

## Top 5 Fixes Before the Final (Presentation) Round

1. **Narrate the grid-cell contract out loud** during the demo ("these are 0.25° pilot
   cells, not villages") so no evaluator reads village/block claims into the UI.
2. **Add two rollback safety-nets before a long demo:** handle a computer that has
   never loaded the XGB artifact (pre-warm), and a graceful offline error card if
   `phase_h_matrix.parquet` is absent — never a blank screen.
3. **Show the ECE/Brier truth** on screen next to the cards (currently in provenance
   JSON only) to preempt "where's the uncertainty?" comments.
4. **Tighten the explain table copy:** cap the delta display with the caveat line
   ("sensitivity ≠ cause") rendered directly under the table (already present, but
   make it unavoidable on mobile).
5. **Lock the demo data-more loudly:** a static "HISTORICAL / DEMO — data through
   2024-09-30" banner in the hero area (currently a small badge) to preempt
   "is this live?" questions.

## Final Output (Phase I gate)

- **Implementation Status:** **PASS**
- **Components Implemented:** serving config/registry/store/model-service/rules/api +
  single-page frontend + demo runner + 39 new tests (68 total) + 3 reports.
- **Test Results:** `python -m pytest tests/ -q` → **68 passed** (2m10s; 29 pre-existing
  Phase A–H + 39 Phase I MVP tests). Demo anchor: revival `10.75_77.5`@2024-08-12 == 0.6047.
- **Frozen Model Integrity:** FREEZE_H digest `4f122044f8710b53`; revival artifact
  (300 trees, depth 6, 64 feats) loaded read-only, imputer train-medians enforced;
  anti-retraining/magic-literal static guards green.
- **Demo Status:** `python -m src.serving.demo` reproduces the full 5-row MVP
  scenario; API probes for /health, /locations, /forecast, /advisory, /explain and
  all error paths verified.
- **Known Limitations:** documented in `reports/MVP_KNOWN_LIMITATIONS.md` (grid-cell
  scope, JJAS-only, no live feed, no auth/cloud/notifications, sensitivity ≠ cause).
- **Evaluator Verdict:** **PASS** for the MVP demo round.
- **Top 5 Fixes Before Presentation:** grid-cell narration · pre-warm + offline
  fallback · on-screen ECE/Brier · unavoidable explain caveat · louder
  HISTORICAL/DEMO banner.
- **STOP POINT REACHED.** Phase I is complete per the approved 12-step plan.

---

**Status: PHASE I COMPLETE — MVP IMPLEMENTATION + EVALUATOR REVIEW DONE. STOPPED per protocol.**