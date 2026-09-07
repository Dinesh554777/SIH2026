# SIH26086 — MVP 36-Hour Execution Plan

Date: 2026-09-07 · Status: **DRAFT FOR APPROVAL — hours are wall-clock estimates for a solo/small team.**

Rules that bind this plan:
- NO LSTM/GRU/Transformer/CNN / new ML; NO retraining.
- The FROZEN models from `FREEZE_H.json` are served as-is.
- Documentation precedes code at every milestone.
- Everything the demo needs already exists in `data/processed` + `models/`.

---

## Hours 0–3: Contracts & freeze verification

1. Audit: load `FREEZE_H.json`, `models/phase_h/B/revival/CONFIG.json`, Group-B feature list.
2. Verify the 64-feature exact list matches `group_features(ph, "B")`.
3. Verify imputation medians (`th_rstd7`, `th_rstd14`, `sp_mean_lag1`) are the frozen train
   medians — write a small pytest-style check file (`tests/test_mvp_serving.py`).
4. Persistence matrix: write `p11/p01` per target (from train) + dseason climatology to a
   single `data/serving/persistence_params.json`. ✅ Gate: determinism on restart.

## Hours 3–6: Serving core (batch/inference), no UI

5. `src/serving/registry.py` — cell registry loader (304 cells), `region_of()` bbox mapping.
6. `src/serving/features.py` — feature row builder for a (cell, date): reuses Phase H
   builders; neighbour-aware NaN handling for `sp_*`; frozen-median imputation.
7. `src/serving/models.py` — `score(cell, date)` → 4 probabilities: 3 persistence +
   XGBoost revival (load `.joblib` once at startup).
8. `src/serving/rules.py` — decision-support table (probability → band → interpretation →
   action) per the rules doc, pure-function.
9. `src/serving/provenance.py` — freeze hash + periods + note into every envelope.
   ✅ Gate: for the demo cell `10.75_77.5` on 2024-08-12, revival == 0.6047 (regression test).

## Hours 6–12: API

10. FastAPI app with the 3 endpoints from `MVP_API_CONTRACT.md` (`/locations`,
    `/cells/{id}/forecast`, `/cells/{id}/advisory`, `/cells/{id}/explain`).
11. Error envelope (404/422/409/500), `generated_at`, band mapping.
12. Tests: contract smoke tests; freeze-parity tests (H_FROZEN parity on 5 pivot dates).
    ✅ Gate: endpoints answer for the demo cells offline.

## Hours 12–18: Demo realization

13. Demo script that walks the exact scenario in `MVP_DEMO_SCENARIO.md` (pivot rows via API).
14. Minimal single-page dashboard (static HTML/CSS/JS, no framework): map-ish picker by cell
    search, 4 cards, Why? panel, provenance footer, disclaimer line.
15. Office-hours degrade path if UI scope slips: keep a JSON/CLI fallback that renders the
    same envelope (the demo judges can still verify via API).
    ✅ Gate: demo script + UI both produce identical envelopes.

## Hours 18–30: Hardening + honesty pass

16. Missing-vs-missing audit: verify no live path ever emits a fake number
    (data_completeness < threshold → 409-style "insufficient data" card).
17. Calibration/band copy sweep: remove any deterministic "will/won't" phrasing.
18. Provenance / freeze audit on every endpoint response.
19. Negative tests: unknown cell, pre-2015 date, non-JJAS day, NaN neighbour feature.
20. Regression: `python -m pytest tests/ -q` stays green (expect 29 + new serving tests).
    ✅ Gate: no green-to-red on existing suite; freeze-parity tests green.

## Hours 30–36: Rehearsal + evaluation prep

21. Full demo rehearsal on the officer script with a timer and a checklist.
22. Team Q&A drill from the 10 judge questions in `MVP_EVALUATOR_REVIEW.md`.
23. Document any extension points deferred (GIS overlay, LLM summary, district aggregates)
    in a short "post-MVP roadmap" section.
24. Final freeze of doc set; handoff.

---

## Milestone gates

| # | Gate | Exit criterion |
| -- | ---- | -------------- |
| G1 | h6 | Serving reproduces pivot numbers incl. 0.6047 for demo cell; determinism check |
| G2 | h12 | 4 endpoints live; freeze-parity smoke green |
| G3 | h18 | Demo runs start-to-finish from `main.py` command |
| G4 | h30 | Full pytest green; honesty/copy audit clean |
| G5 | h36 | Rehearsal passed; docs final |

## Risk register (top risks for the 36 hours)

| Risk | Likelihood | Impact | Mitigation |
| ---- | ---------- | ------ | ---------- |
| Spatial neighbour features diverge from Phase H | medium | high (wrong numbers) | Regression test pins demo-cell revival=0.6047; reuse exact builders |
| UI scope creep | high | medium | CLI fallback guaranteed by gate G3; UI is polish |
| Judge interprets persistence as "not AI" | medium | medium | Narrative: calibrated persistence is a defensible product; ML revival card is the differentiator |
| Fake-certainty copy leaking in | medium | high | Copy sweep at h18–30 + band language enforcement |
| Live data system unavailable during demo | low | high | Demo is precomputed offline on frozen research data by design |

## Dependency on approvals

None beyond this doc set + the product-spec choices (user = extension officer; horizon =
same-day observation cutoff; GIS = grid cells, not villages). If the human amends any of
these, hours 0–3 re-run the contract check only.