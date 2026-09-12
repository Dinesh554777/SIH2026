# PHASE I-A — BACKEND FOUNDATION

**Project:** SIH2026 — Hyperlocal Probabilistic Monsoon Decision-Support System
**Date:** 2026-09-12
**Status:** COMPLETE (awaiting human review before Phase I-B)

---

## 1. Objective

Prepare a clean, runnable backend foundation (Python + FastAPI + Uvicorn) that reuses the
existing frozen scientific pipeline and is ready to connect **PostgreSQL** and **Groq** in
later phases. The existing `src/serving/` MVP was inspected and extended, not rebuilt.

## 2. Architecture

Reused as-is (no modification to the scientific pipeline):

```
src/serving/
  api.py      FastAPI app + routes                    (extended)
  config.py   env-based configuration                 (extended)
  registry.py CellRegistry - 304 pilot grid cells     (unchanged)
  store.py    ObservationStore - frozen Phase H matrix (unchanged)
  models.py   ModelService - frozen inference         (unchanged, inference lives here)
  rules.py    bands / cards / decision-support        (unchanged)
  demo.py     reproducible demo scenario              (unchanged)
data/ ...     FREEZE_H.json, phase_h_matrix.parquet    (unchanged)
models/phase_h/B/revival/... frozen XGBoost+imputer   (unchanged)
tests/ ...    scientific + MVP tests                  (unchanged)
```

Added during this phase:

```
src/serving/schemas.py     Pydantic response models for /health, /api/v1/cells
requirements.txt           backend runtime dependencies
tests/test_backend_foundation.py   tests for the new endpoints
reports/PHASE_I_A_BACKEND_FOUNDATION.md   this report
```

Target architecture (later phases):

```
Frontend
   -> FastAPI
   -> PostgreSQL (database layer prepared in src/database/, not wired yet)
   -> Frozen ML inference (ModelService, unchanged)
   -> Groq API (configuration prepared only, not implemented)
```

## 3. Files Changed / Added

| File                          | Change |
|-------------------------------|--------|
| `src/serving/api.py`          | `/docs` now primary docs URL (+ `/api/docs` GET redirect); `/health` extended with honest `components` block (API/model/data/database); added `GET /api/v1/cells`; Pydantic `response_model`s |
| `src/serving/config.py`       | Added `ENVIRONMENT`, `GROQ_API_KEY` (placeholder), `MODEL_DIR`, `DATA_DIR`; kept legacy `SIH_*` overrides and existing names |
| `src/serving/schemas.py`      | **NEW** – response schemas (`HealthResponse`, `CellsResponse`, `CellEntry`, component models), `extra="allow"` so the MVP contract is unchanged |
| `requirements.txt`            | **NEW** – pinned runtime deps (fastapi, uvicorn, pydantic, pandas, numpy, joblib, xgboost, SQLAlchemy, psycopg2, alembic) |
| `.env.example`                | Added `ENVIRONMENT`, `MODEL_DIR`, `DATA_DIR`, `GROQ_API_KEY` placeholders; documented `DATABASE_URL` (handled by the database layer) |
| `tests/test_backend_foundation.py` | **NEW** – 7 tests for `/health`, `/api/v1/cells`, `/docs`, redirect, 405/404 |

`inference.py` was intentionally **not** added: `ModelService.predict` in `models.py` is
already the inference layer; duplicating it would violate the "do not duplicate existing
modules" rule.

## 4. Endpoints

| Method | Path                     | Description                                    |
|--------|--------------------------|------------------------------------------------|
| GET    | `/health`                | API/model/data/database status (honest)        |
| GET    | `/api/v1/cells`          | All 304 pilot cells (registry-derived)         |
| GET    | `/docs`                  | Swagger UI (OpenAPI at `/openapi.json`)        |
| GET    | `/api/docs`              | Redirect to `/docs` (back-compat)              |
| GET    | `/locations`             | Unchanged legacy cell list (frontend uses it)  |
| GET    | `/api/v1/cells/{id}/forecast|advisory|explain` | Unchanged inference endpoints (contract intact) |

`/health` behaviour (no faked status):

```json
{
  "status": "ok",
  "components": {
    "api":      {"status": "ok"},
    "model":    {"status": "ok", "freeze_digest": "...", "selected_models": {...}},
    "data":     {"status": "ok", "n_cells": 304, "observation_period": {...}},
    "database": {"status": "not_configured", "dsn_set": false}
  }
}
```

- If `DATABASE_URL` is unset → `database.status = not_configured`.
- If set but unreachable → `database.status = error` (never "ok").
- If model/data artifacts fail to load → `status = degraded` with per-component `error` detail.

## 5. Environment Variables

| Variable        | Purpose                              | Default     |
|-----------------|--------------------------------------|-------------|
| `ENVIRONMENT`   | development / test / production      | development |
| `MODEL_DIR`     | models directory                     | `./models`  |
| `DATA_DIR`      | data directory                       | `./data`    |
| `GROQ_API_KEY`  | **placeholder only** — later phase   | *(empty)*   |
| `DATABASE_URL`  | consumed by `src.database.config`    | *(unset)*   |

Legacy overrides `SIH_DATA_ROOT` / `SIH_MODELS_ROOT` / `SIH_PROJECT_ROOT` still work.
`.env.example` contains placeholders only; `.env` (real values) is git-ignored. No real
Groq key or database password appears anywhere in source control.

Groq is **not implemented** in this phase (Step 5 requirement): only configuration support
is prepared.

## 6. Startup Command

```bash
# from the project root
python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000
# or
python -m src.serving.api
```

Then open `http://127.0.0.1:8000/docs`, `http://127.0.0.1:8000/health`,
`http://127.0.0.1:8000/api/v1/cells`.

## 7. Test Results

Full suite: `python -m pytest -q` → **81 passed, 14 skipped** (the 14 skipped are
PostgreSQL tests, gated until a test DSN exists), 1 pre-existing numpy warning.

New backend tests pass:

```
tests/test_backend_foundation.py .......   7 passed
tests/test_mvp_api.py .............         14 passed   (existing, unchanged)
tests/test_mvp_serving.py ................  14 passed
tests/test_database_config.py .....         5 passed
```

Live verification with the running uvicorn server (127.0.0.1:8000):

| Request                                         | Result |
|--------------------------------------------------|--------|
| `GET /health`                                    | 200 — `status=ok`, `database.status=not_configured` |
| `GET /api/v1/cells`                              | 200 — 304 cells (stopstep regions KA/MH/TN) |
| `GET /docs`                                      | 200 — Swagger UI |
| `GET /api/docs`                                  | 307 redirect → `/docs` |
| `GET /api/v1/cells/99.99_99.99/forecast` (unknown cell) | 404 `unknown_cell` |
| `GET .../forecast?date=notadate` (invalid)       | 422 `invalid_date` |
| `GET .../forecast?date=2024-12-31` (outside season) | 422 `outside_season` |
| `POST /api/v1/cells` (wrong method)              | 405 |
| `GET /api/v1/does-not-exist`                     | 404 |
| `GET .../forecast?date=2024-08-12` (valid demo)  | 200 — revival p=0.60468 (matches frozen test 0.6047) |

## 8. Known Limitations

- **Database**: PostgreSQL layer exists in `src/database/` (models, migrations, seed,
  repository, tests) but is **not connected** to the app yet — hence `not_configured`.
  Connect + wire in the database phase.
- **Groq**: not implemented; `GROQ_API_KEY` is prepared but unused.
- **`/api/docs`**: redirect serves GET only (browsers use GET; HEAD returns 404).
- **Frontend**: still calls `/locations` (kept). It can be migrated to `/api/v1/cells` later.
- **Health latency**: when a DSN is set, `/health` performs a real DB ping (5s connect
  timeout); offline it is instant.
- **Model/data availability** is derived from component construction — a missing artifact
  degrades the health report rather than failing startup.

# COMPLETION RESPONSE (Phase I-A)

## Backend Status

PASS

## Endpoints Tested

- `GET /health` — 200, `database: not_configured` (honest, DSN unset)
- `GET /api/v1/cells` — 200, 304 cells
- `GET /docs` — 200 Swagger UI
- `GET /api/docs` — 307 redirect
- Invalid: unknown cell 404, malformed date 422, out-of-season 422, wrong method 405, unknown route 404

## Test Results

`python -m pytest -q` → 81 passed, 14 skipped (DB-gated), 1 pre-existing warning. New
backend tests: 7/7 pass. Live uvicorn verification above.

## Files Added/Changed

Added: `src/serving/schemas.py`, `requirements.txt`, `tests/test_backend_foundation.py`,
`reports/PHASE_I_A_BACKEND_FOUNDATION.md`.
Changed: `src/serving/api.py`, `src/serving/config.py`, `.env.example`.

## Problems Encountered

- `/api/docs` HEAD request returns 404 (GET redirect works) — accepted, Browsers use GET.
- `Invoke-WebRequest` unusable non-interactively; switched to `curl.exe` for live checks.
- None affecting the scientific pipeline; all frozen artifacts and inference untouched.

## Recommended Next Phase

Connect the prepared PostgreSQL layer: set up dev/test DBs, run Alembic migrations,
seed the 304 cells + frozen provenance, persist forecasts/advisories via the repository,
and surface real database status in `/health`.

STOP — waiting for human review before starting Phase I-B.