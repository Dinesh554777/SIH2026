# MVP Final Handoff (SIH26086)

Status: **Phase I COMPLETE, frozen** · Date: 2026-09-08 · Stop point honored.

## Runbook

| Action | Command |
|---|---|
| All tests | `python -m pytest tests/ -q` (expected: 69 passed) |
| Demo (reproducible) | `python -m src.serving.demo` |
| Export G1 params (audit snapshot) | `python -m src.serving.persistence_params` |
| Run app | `python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000` |
| UI | http://127.0.0.1:8000 (demo buttons on the controls panel) |
| Docs | http://127.0.0.1:8000/api/docs (FastAPI) |
| Rehearsal prep | `reports/MVP_REHEARSAL_SCRIPT.md` |

## What is frozen (never to be touched in a demo rerun)

- `data/processed/FREEZE_H.json` — architecture + freeze note; digest `4f122044f8710b53`
- `models/phase_h/B/revival/{xgboost,imputer}.joblib` + `CONFIG.json` — 64-feature DNN of trust
- `data/processed/phase_h_matrix.parquet` — 370,880×97, 304 cells, 2024 held out
- `data/serving/persistence_params.json` — frozen persistence/climatology snapshot (G1)

## Where the honesty lives

- `reports/MVP_KNOWN_LIMITATIONS.md` (grid cells ≠ villages; JJAS only; no live feed)
- `reports/MVP_MODEL_PROVENANCE.md` (every number's trace, digest included)
- `reports/PHASE_I_EVALUATOR_REVIEW.md` (10-criteria PASS + Top-5 pre-demo fixes)
- `reports/POST_MVP_ROADMAP.md` (deferred work, no scope creep)

## Handoff notes for the presenting team

1. Do not retrain, re-freeze, or re-tune anything ahead of the demo.
2. Pre-warm the app once; a cold first load takes ~2 s.
3. If a judge asks "is this live?": answer "historical/demo by design, frozen pipeline,
   2024 held out" — the banner already says it.
4. The single strongest claim: *frozen, leak-free, per-cell probabilistic output —
   reproduced end-to-end by one command.*

## Doc inventory (reports/)

Completed in Phase I: `MVP_*` planning set (8), `PHASE_I_IMPLEMENTATION_REPORT.md`,
`MVP_MODEL_PROVENANCE.md`, `MVP_KNOWN_LIMITATIONS.md`, `PHASE_I_EVALUATOR_REVIEW.md`,
`MVP_REHEARSAL_SCRIPT.md`, `POST_MVP_ROADMAP.md`, this handoff.
Referenced: Phase A–H completion reports & model-selection/validation docs.

---

**FINAL: 69 tests expected green, demo deterministic, 2024 untouched, docs complete. Handoff.