# SIH26086 — Phase I-A: PostgreSQL Application Database Architecture

Date: 2026-09-12 · Status: **PROPOSED — awaiting human approval (STEP 1 gate)**

## 1. Existing persistence (what is in the repo today)

| Persistence mechanism | Scope | Notes |
|---|---|---|
| `data/processed/phase_h_matrix.parquet` | Scientific feature matrix (370,880×97, 304 cells, JJAS 2015–2024) | Read-only source for inference; **stays outside PostgreSQL** |
| `data/processed/FREEZE_H.json` | Freeze architecture/digest `4f122044f8710b53` | Provenance source of truth |
| `models/phase_h/B/revival/*.joblib` | Frozen revival model + imputer (64 feats) | Read-only artifacts |
| `data/serving/persistence_params.json` | Frozen persistence/climatology snapshot (gate G1) | Audit/mirror only |
| `src/serving/*` | In-memory registry (304 cells), store, ModelService | Loaded per process; **no app-level record keeping** |

There is currently **no database layer**. Forecasts/advisories are computed on demand and
returned by FastAPI; nothing is written for later retrieval, audit, or user-facing history.

## 2. Environment facts (verified)

- **PostgreSQL 18** installed as a Windows service `postgresql-x64-18`, **running**,
  accepting connections on `127.0.0.1:5432` (`pg_isready` OK).
  Client binaries: `C:\Program Files\PostgreSQL\18\bin\psql.exe` (not on PATH).
- **Docker CLI present but daemon OFF** (fallback only; not required while the native
  service runs).
- Python deps already installed: `SQLAlchemy 2.0.36`, `alembic 1.14.0`,
  `psycopg2-binary 2.9.10` (+ `asyncpg` if we later go async).
- **Not resolved yet (required at implementation):** superuser password / dedicated app
  role for the local PostgreSQL 18 service. Will use the `postgres` superuser once,
  interactively, to create role + dev & test databases — credentials stored only via
  `DATABASE_URL`/`.env`, never in source.

## 3. Strategy: extend, do not replace

PostgreSQL is an **application persistence layer**, layered *under* FastAPI — not a
replacement for the scientific Parquet pipeline.

```
Scientific Data / Parquet  (data/processed/*.parquet)
        │  read-only
        ▼
Feature + Inference layer  (src/serving/models.py, store.py, registry.py)
        │  frozen models produce probabilities
        ▼
Forecast / Advisory result (rules.py envelope)
        │  write
        ▼
PostgreSQL  (database/ — locations, forecasts, advisories, model_versions)
        │  read
        ▼
FastAPI      (src/serving/api.py)
        │
        ▼
Frontend     (frontend/)
```

**Non-negotiable contracts**
- Inference code, frozen models, `FREEZE_H.json`, feature engineering, labels and
  evaluation **are not modified**.
- Parquet remains the scientific source of truth; PostgreSQL stores **application
  records** (which forecast was produced, for which cell/date, by which frozen
  model, with what advisory text).
- Observation history is **not** replicated into a scientific `observations` table.
  Only a compact JSONB *observation snapshot* (evidence + current signal +
  completeness) is kept per forecast row for application-level traceability.

## 4. Proposed schema

Conventions: surrogate `BIGSERIAL id` PKs, natural unique keys enforced, all FK
columns typed, probabilities `NUMERIC(6,4)` (0.0000–1.0000), timestamps
`TIMESTAMPTZ`, `cell_id` stored exactly as the registry format `"<lat>_<lon>"`.

### 4.1 `locations` — 304 pilot grid cells (seeded from registry)

| Column | Type | Constraints / notes |
|---|---|---|
| id | BIGSERIAL | PK |
| cell_id | VARCHAR(32) | UNIQUE NOT NULL (matches registry + `CELL_ID_RE` regex) |
| latitude | DOUBLE PRECISION | NOT NULL |
| longitude | DOUBLE PRECISION | NOT NULL |
| region | VARCHAR(16) | NOT NULL; bbox-derived grouping, non-authoritative |
| state | VARCHAR(64) | NULL; reserved for a future official admin mapping (registry has none today) |
| is_active | BOOLEAN | NOT NULL DEFAULT true |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |

### 4.2 `model_versions` — frozen model provenance (seeded from FREEZE_H.json at boot-time)

| Column | Type | Constraints / notes |
|---|---|---|
| id | BIGSERIAL | PK |
| model_name | VARCHAR(32) | NOT NULL (`persistence` \| `xgboost`) |
| target | VARCHAR(16) | NOT NULL (`onset` \| `break` \| `revival` \| `dry_spell`) |
| feature_group | VARCHAR(32) | NULL (`frozen_reference` \| `B_temporal`) |
| artifact_version | VARCHAR(64) | NULL (e.g., `xgboost_groupB_64feats`, revival artifact CONFIG `trained_at`) |
| artifact_digest | VARCHAR(64) | NOT NULL (FREEZE_H sha256 first 16 hex: `4f122044f8710b53`) |
| training_period | VARCHAR(32) | NOT NULL (`2015-2021`) |
| validation_period | VARCHAR(32) | NOT NULL (`2022-2023`) |
| test_period | VARCHAR(32) | NOT NULL (`2024`) |
| validation_ece | NUMERIC(10,8) | NOT NULL (per-target frozen ECE) |
| validation_brier | NUMERIC(12,8) | NOT NULL (per-target frozen Brier) |
| is_frozen | BOOLEAN | NOT NULL DEFAULT true |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |

UNIQUE constraint: `(model_name, target, artifact_digest)` — immutable provenance rows
(insert-on-startup, `ON CONFLICT DO NOTHING`).

### 4.3 `forecasts` — persisted forecast results

| Column | Type | Constraints / notes |
|---|---|---|
| id | BIGSERIAL | PK |
| cell_id | VARCHAR(32) | FK → locations.cell_id, NOT NULL |
| forecast_date | DATE | NOT NULL (the observation day _t_; same-day cutoff) |
| generated_at | TIMESTAMPTZ | NOT NULL |
| onset_probability | NUMERIC(6,4) | NOT NULL |
| break_probability | NUMERIC(6,4) | NOT NULL |
| revival_probability | NUMERIC(6,4) | NOT NULL |
| dry_spell_probability | NUMERIC(6,4) | NOT NULL |
| dominant_state | VARCHAR(16) | NULL (`onset`/`break`/`revival`/`dry_spell`) |
| band | VARCHAR(16) | NULL (`low`/`moderate`/`high`/`very_high`, CHECK constraint) |
| model_version_id | BIGINT | FK → model_versions.id, NOT NULL |
| prediction_mode | VARCHAR(32) | NOT NULL DEFAULT `historical/demo` |
| observation_snapshot | JSONB | NOT NULL DEFAULT `'{}'` (evidence + current_dignal + completeness; NOT the scientific matrix) |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |

UNIQUE constraint: `(cell_id, forecast_date, model_version_id)` — idempotent upsert.

### 4.4 `advisories` — decision-support text per forecast

| Column | Type | Constraints / notes |
|---|---|---|
| id | BIGSERIAL | PK |
| forecast_id | BIGINT | FK → forecasts.id, NOT NULL ON DELETE CASCADE |
| advisory_type | VARCHAR(32) | NOT NULL (`summary` \| `card`) |
| state | VARCHAR(16) | NOT NULL for `card` rows; `summary` rows use `summary` |
| band | VARCHAR(16) | NULL; CHECK same as forecasts.band |
| probability | NUMERIC(6,4) | NULL (card rows) |
| message | TEXT | NOT NULL (`summary`: dominant-state sentence; `card`: interpretation + suggested action) |
| language | VARCHAR(8) | NOT NULL DEFAULT `en` |
| created_at | TIMESTAMPTZ | NOT NULL DEFAULT now() |

UNIQUE constraint: `(forecast_id, advisory_type, state)`.

## 5. Relationships

```
locations 1 ──── N forecasts N ──── 1 model_versions
forecasts 1 ──── N advisories
```
- `forecasts.cell_id` → `locations.cell_id` (natural FK for readability).
- `forecasts.model_version_id` → `model_versions.id` (which frozen model produced it).
- `advisories.forecast_id` → `forecasts.id` (ON DELETE CASCADE).

## 6. Indexes

| Table | Index | Purpose |
|---|---|---|
| locations | uq_locations_cell_id (cell_id) | unique lookup by id |
| model_versions | uq_model_versions (model_name, target, artifact_digest) | idempotent seed |
| forecasts | uq_forecasts (cell_id, forecast_date, model_version_id) | idempotent upsert + uniqueness |
| forecasts | ix_forecasts_cell_date (cell_id, forecast_date DESC) | primary query path (cell history) |
| forecasts | ix_forecasts_date (forecast_date) | date-range queries / polling |
| forecasts | ix_forecasts_model_version (model_version_id) | FK join |
| advisories | ix_advisories_forecast (forecast_id), uq (forecast_id, advisory_type, state) | fetch bundle for a forecast |

## 7. Migration & seed strategy (Alembic + SQLAlchemy 2.0)

- `alembic.ini` at repo root; versions in `database/migrations/versions/`.
- `database/` layout:
  ```
  database/
    migrations/
      env.py            (reads DATABASE_URL)
      versions/
        0001_initial.py (CREATE tables, FKs, CHECK constraints, indexes)
    models.py           (SQLAlchemy 2.0 ORM models: Location, ModelVersion, Forecast, Advisory)
    repository.py       (app-facing write/read helpers; used by API)
    seed.py             (`python -m src.database.seed`)
  ```
  (location `src/database/` if the repo prefers the `src/` layout — see decision note)
- **Reproducibility test:** empty DB → `alembic upgrade head` → schema → `seed` (304
  cells + 4 model_versions from registry & FREEZE_H.json) → application connects.
- Seed uses the **authoritative registry** (`CellRegistry.from_matrix` → 304 rows) —
  never hand-typed. Uniqueness of `cell_id` asserted (304 unique).
- Probabilities stored via `NUMERIC(6,4)` (4 decimal places ≈ the API's rounding).

## 8. Development vs production databases

| Environment | Database | Connection resolution |
|---|---|---|
| Dev | `sih2026_app` on localhost:5432 (PostgreSQL 18 service) | `DATABASE_URL` (`.env`), else PG* env vars |
| Test | `sih2026_app_test` on localhost:5432 | `DATABASE_URL_TEST`, else `.../app_test`. Tests run against **test DB only**; never dev/prod |
| Prod | `sih2026_app_prod` (future) | `DATABASE_URL` injectable; no source defaults |

- Connection string uses `postgresql+psycopg2://` (sync, matches current sync FastAPI).
- Tests create/drop schema via Alembic in the test database (empty-DB init tested), and
  use SQLAlchemy `create_all`-check to confirm migrations match models.

## 9. Environment configuration & security

- **Env vars only** for credentials: `DATABASE_URL`, `PGHOST`, `PGPORT`, `PGUSER`,
  `PGPASSWORD`, `PGDATABASE` (DSN composed if `DATABASE_URL` unset). Never hardcode
  user/host/password/URLs.
- Create `.env.example` (placeholders only). `.gitignore` already covers `.env`,
  `.env.local` ✓.
- `postgres` superuser password never written to source; used once interactively to
  create an app role (e.g., `sih2026_app` with password supplied at runtime) and the
  dev+test databases, then only the role runs the app.

## 10. Backup considerations (documented for prod)

- `pg_dump` nightly + WAL archiving when a production server exists;
  `pg_restore` for recovery. Dev DB disposable (recreatable by migrate+seed).
- Freeze digest + artifact digests on every row make the app DB re-derivable — the
  Parquet models remain the recoverable core.

## 11. Open decisions to confirm before implementation

1. Package location: repo-root `database/` vs `src/database/`. **Proposal: `src/database/`**
   to match the repo's flat `src/` layout (alembic.ini still at root).
2. Need one interactive step to create role + dev/test DBs on the local PostgreSQL 18
   (superuser password required once).
3. Advisor storage: relational rows (`summary` + 4 `card` rows) — adopted (section 4.4).

---

**Proposed schema above. STOP — awaiting human approval to implement
(Steps 2–7: schema, migrations, env, seed 304 cells, DB tests, docs, completion gate).**