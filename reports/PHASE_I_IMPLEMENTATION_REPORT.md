# PHASE I — MVP Implementation Report

**Date:** 2026-09-08 · **Project:** SIH26086 — Hyperlocal Monsoon Onset/Break Probabilistic Decision-Support (YELLOW)
**Scope:** Smallest reliable hackathon MVP — real frozen inference, real numbers, no fake dashboard.

## 1. Implementation Status

**PASS** (component, prose below).

All deliverables from the approved 12-step build order are implemented and verified
end-to-end. Inference is real: every probability in the UI, API and demo is computed
on demand from the frozen Phase H artifacts (`data/processed/FREEZE_H.json`,
`models/phase_h/B/revival/*`). No probabilities are hardcoded, no models are retrained,
and the 2024 held-out test set remains unseen by the pipeline.

## 2. Components Implemented

| Component | Files | Status |
|---|---|---|
| Frozen-infrastructure config (paths, modes, spatial-unit contract) | `src/serving/config.py` | DONE |
| Cell registry (304 pilot cells, region via bbox, grid-cell disclaimer) | `src/serving/registry.py` | DONE |
| Observation store (per-cell timeline, previous-day lookup, completeness) | `src/serving/store.py` | DONE |
| Model service (persistence + climatology + frozen XGB revival, sensitivity, provenance) | `src/serving/models.py` | DONE |
| Decision-support rules engine (bands, phrases, v1) | `src/serving/rules.py` | DONE |
| FastAPI service + HTML mount (`/health`, `/locations`, `/api/v1/cells/{id}/forecast`, `/advisory`, `/explain`) | `src/serving/api.py` | DONE |
| Minimal frontend (4 cards, bands, current signal, guidance, why, provenance, demo buttons) | `frontend/` | DONE |
| Reproducible demo runner | `src/serving/demo.py` | DONE |
| Test suite (39 new; 68 total green) | `tests/test_mvp_*.py` | DONE |
| Reports | `reports/PHASE_I_IMPLEMENTATION_REPORT.md`, `MVP_MODEL_PROVENANCE.md`, `MVP_KNOWN_LIMITATIONS.md` | DONE |

### 2.1 Model selection (unchanged from freeze)

- `onset`   → **persistence** (`KEEP_FROZEN_REFERENCE`)
- `break`   → **persistence** (`KEEP_FROZEN_REFERENCE`)
- `dry_spell` → **persistence** (`KEEP_FROZEN_REFERENCE`)
- `revival` → **XGBoost Group B_temporal** (frozen revival artifact, `CANDIDATE_FOR_FREEZE` frozen on 2026-09-07)

Decision: keep frozen reference.
No hyperparameter, feature list, imputation or training window has been modified.

## 3. How a Forecast Is Built (deterministic, ordered)

1. Monday-to-Sunday window is irrelevant here; the unit of time is a calendar day.
2. For a request `(cell_id, date)` the API resolves the cell, validates the date is
   ISO-8601 and inside JJAS (Jun 1 – Sep 30) and present in the cell's timeline,
   then checks feature completeness (`>= 0.9` on the 64 revival features) — else a
   `404 date_not_available` or `409 insufficient_data` error envelope is returned.
3. Persistence targets use the frozen two-state Markov transition matrix
   P(y_t | y_{t-1}) computed only on train (2015–2021). If the calendar day is the
   first JJAS day (dseason==1) the target probability falls back to the cell-dseason
   climatological frequency (frozen `build_climatology`), matching the Phase G/H
   baseline exactly.
4. Revival reads the same-day observation row, applies the FROZEN median imputer
   (train-only statistics), feeds the 64 features **in CONFIG.json order** into the
   frozen XGBClassifier, and returns `predict_proba[:,1]`.
5. Bands (`low`/`moderate`/`high`/`very_high`), interpretations/actions (rules v1),
   current signal and sensitivity explanation are computed deterministically from the
   probability vector and the observation row.
6. Every response carries model provenance: freeze digest, model per target,
   feature group, n_features, observation date, data mode, imputation note,
   validation ECE/Brier, horizon note.

## 4. API Contract (as built, matches `reports/MVP_API_CONTRACT.md`)

| Endpoint | Returns |
|---|---|
| `GET /health` | status, data_mode, freeze_digest |
| `GET /locations` | 304 pilot cells (cell_id, lat, lon, region, observation_period), spatial_unit, data_mode |
| `GET /locations/{cell_id}` | single-cell metadata |
| `GET /api/v1/cells/{cell_id}/forecast?date=` | per-target probability, band, band_meaning, model, provenance, confidence |
| `GET /api/v1/cells/{cell_id}/advisory?date=` | dominant state, summary, per-state items (interpretation, action, expert validation tags), current signal, disclaimer |
| `GET /api/v1/cells/{cell_id}/explain?date=` | target revival only, sensitivity table (feature, value, train median, delta pp), non-causal caveat |
| `GET /` | single-page HTML app (mounted when `frontend/` exists) |

Error envelope (never a fabricated probability): `{"error": {"code", "message", "detail"}}` with
`unknown_cell` (404), `date_not_available` (404), `invalid_date` (422),
`outside_season` (422), `insufficient_data` (409).

## 5. Demo Scenario Reproduced (from `reports/MVP_DEMO_SCENARIO.md`)

Demo cell `10.75_77.5` (TN pilot cell). Run with `python -m src.serving.demo`.

| Date | Rain_t (mm) | Break % | Revival % | Dry-spell % | Story |
|---|---|---|---|---|---|
| 2024-06-07 | 40.1 | 4.8 | 0.0 | 2.1 | False onset (onset P stays low) |
| 2024-08-08 | 0.0 | 90.8 | 0.0 | 91.6 | Dry-spell eve: persistence cards sticky |
| 2024-08-11 | 0.23 | 90.8 | 0.0 | 91.6 | Trace rain, revival quiet |
| **2024-08-12** | 2.97 | 90.8 | **60.5 (high)** | 91.6 | **Revival day — ML card fires** |
| 2024-09-29 | 8.91 | 90.8 | **98.6 (very high)** | 91.6 | Late-season second revival |

Hard check embedded in the demo + test: revival on 2024-08-12 equals the frozen
2024 test pass value `0.6047` exactly (assert tolerance 1e-3).

## 6. Test Results

Comprehensive: `python -m pytest tests/ -q` → **68 passed** (~2m10s, includes the 29
pre-existing Phase A–H tests).

New test modules (39 tests):
- `tests/test_mvp_serving.py` — determinism, target mapping, frozen artifact spec,
  feature order /name parity with CONFIG.json, revival parity 0.6047, persistence
  parity vs `baseline_predictions.parquet`, dseason==1 climatology, frozen median
  imputation parity, band boundaries, rules completeness, advisory bundle shape,
  sensitivity ground-truth.
- `tests/test_mvp_api.py` — health, locations (304, regions {TN,MH,KA}, admin_note),
  forecast/advisory/explain output shape, forecast==direct-inference equality,
  default-latest date, 404/422/409 error paths, traversal-safe cell handling.
- `tests/test_mvp_integrity.py` — static guards: no `fit(`/`.train(`/grid-search in
  inference files; no fresh model construction; no probability literals in
  inference path; no LLM tokens; frozen artifacts exist and checksum; FREEZE_H
  schema agrees with serving config; data mode never claims live.
- `tests/test_mvp_demo.py` — demo anchor value, pivot narrative, demo runner.
- Scientific integrity guarantees are enforced by `tests/test_mvp_integrity.py`.

## 7. Frozen Model Integrity

- `FREEZE_H.json` — sha256 digest recorded at runtime: `4f122044f8710b53` (first 16 hex).
- Revival artifact (`CONFIG.json` = 64 features, imputer stats, hyperparameters)
  is read-only at runtime; serving only `joblib.load`s the `.joblib` weights and
  never mutates `models/` or `data/processed/`.
- Serving loads through the exact `build_climatology` / `build_persistence_transitions`
  helpers used at freeze time, so persistence equals the frozen baseline by construction.

## 8. Performance

- Boot: single module-scope loads of matrix (~370k rows), freeze JSON, imputer and
  XGB model (≈ 2 s); all singletons cached (`default_store/registry/service`).
- Per-request: O(64 features) imputation + tree eval (µs) + one matrix row lookup;
  no DB, no microservices, no network calls.
- Static assets (HTML/CSS/JS) mounted read-only from `frontend/`.

## 9. Security

- Inputs validated: cell id regex + registry membership; date parsed strictly
  (ISO date, then JJAS + availability checks) → path traversal impossible.
- No user code execution, no arbitrary file reads (all paths are constants from
  `config.py`), artifact access is read-only, no secrets in source, no env secrets
  required, no auth surface exposed (intentionally out of scope).
- Advisories are framed as *decision support*, never as guarantees; disclaimers are
  returned in every advisory payload.

## 10. How to Run

```
python -m pytest tests/ -q            # 68 passed
python -m src.serving.demo            # reproduces MVP_DEMO_SCENARIO end-to-end
python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000
# open http://127.0.0.1:8000  ->  demo buttons: False onset / Dry spell eve / Revival
```

## 11. Deliverables Checklist (Phase I spec)

- [x] Smallest reliable MVP (single service, single matrix, real inferences)
- [x] Real inference — no fake dashboard, no hardcoded numbers
- [x] Frozen architecture honored; no retraining
- [x] Deterministic pipeline with explicit timestamp; same-day-observation assumption
- [x] Backend minimum endpoints (all from contract)
- [x] Historical/demo mode clearly labelled; no fabricated live data
- [x] 304 grid cells; "pilot cell / grid cell" language everywhere; no villages/blocks
- [x] Deterministic decision-support engine, versioned, separate from ML, testable
- [x] Advisories framed as decision support; exact sample phrasings used
- [x] Frontend minimal: 4 cards, bands, uncertainty, current signal, guidance, why, model
- [x] Explainability uses frozen model sensitivity; descriptive, non-causal
- [x] No LLM in the numeric/decision path
- [x] Provenance in every response
- [x] Explicit error handling; never fabricated probabilities
- [x] Tests pass; scientific integrity guards included
- [x] Reports delivered