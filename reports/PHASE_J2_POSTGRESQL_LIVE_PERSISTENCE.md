# Phase J2 — PostgreSQL Live Observation Persistence Report

**Gate:** J2 — Live Observation Persistence (durable storage for the live pipeline)
**Previous gates:** J0 PASS (audit), J1 PASS — LIVE CONNECTIVITY BLOCKED (ingestion layer in `src/ingestion/`)
**Date:** 2026-09-12
**Author:** OpenCode automated pipeline

---

## 1. Objective

Add PostgreSQL persistence for (a) normalized live observations and (b) ingestion-run
metadata/status, establishing durable storage for the future live forecasting pipeline.
Scope strictly excludes J3 feature engineering, model inference, J4/J5/J6, Groq and any
change to the frozen Phase H artifacts.

## 2. Tables added

| Table | Purpose |
|---|---|
| `observations` | Normalized live daily rainfall observations (one row per cell + day + source) |
| `ingestion_runs` | Provenance/status of every ingestion cycle (SUCCESS/PARTIAL/BLOCKED/FAILED) |

Both are defined in `src/database/models.py` (ORM) and materialized by Alembic
migration `0002`, which extends the existing Phase I-B schema without touching
`cells` / `model_metadata` / `forecasts` / `advisories` structures.

## 3. Schema / constraints / indexes

`observations`:
- columns: `id`, `cell_id` (FK → `cells.cell_id`, RESTRICT), `observation_time`
  (`timestamp with time zone`), `latitude`, `longitude`, `rainfall_mm_day`,
  `source`, `retrieved_at` (`timestamp with time zone`), `quality_flag`,
  `created_at`
- `UNIQUE (cell_id, observation_time, source)` = `uq_observations_cell_time_source`
- CHECK `rainfall_mm_day >= 0`; CHECK `quality_flag IN ('valid','missing','invalid','stale','future')`
- indexes: `ix_observations_cell_time`, `ix_observations_time`, `ix_observations_source`

`ingestion_runs`:
- columns: `id`, `source`, `started_at`, `completed_at`, `status`,
  `rows_received`, `rows_inserted`, `rows_rejected`, `error_type`,
  `error_message` (text), `metadata` (JSON), `created_at`
- CHECK `status IN ('RUNNING','SUCCESS','PARTIAL','FAILED','BLOCKED')`
- index: `ix_ingestion_runs_started_at`

Verified live against the database (information_schema + pg_constraint + pg_indexes):
`observation_time` and `retrieved_at` are real `timestamp with time zone`; unique/check
constraints and all indexes present.

## 4. Migration

- `database/migrations/versions/0002_live_ingestion.py` (revision `0002`, down `0001`)
- Deterministic, reversible, transaction-safe; does not modify Phase I-B tables or any
  scientific artifact.
- Executed on the live DB: `alembic upgrade head` → `0002 (head)`.
- Reversibility proven live: `alembic downgrade 0001` removed both tables, then
  `alembic upgrade head` re-created them cleanly.

## 5. Repository layer

`src/database/ingestion_repository.py` (no forecasting logic):

Observations — `insert_observation`, `bulk_insert_observations`, `get_latest_observation`,
`get_observation_history`, `get_observations_in_range`, `count_observations`.
Ingestion runs — `create_ingestion_run`, `update_ingestion_run`, `get_ingestion_run`,
`get_latest_ingestion_runs`.
Status mapping — `ingestion_status_for_result(IngestionResult) -> (status, error_type)`.

Transaction discipline: all repository functions FLUSH but do not commit; the pipeline
owns the transaction so observations + run status commit atomically. Bulk insert is a
single multi-row `INSERT ... ON CONFLICT DO NOTHING` (efficient for the 304-cell pilot).

## 6. Idempotency strategy

- Natural key `(cell_id, observation_time, source)` enforced by a DB unique constraint.
- Inserts use PostgreSQL `ON CONFLICT DO NOTHING` — repeated identical ingestion never
  duplicates rows; no destructive "delete-and-reinsert" behavior anywhere.
- Proven by tests: single insert twice → 1 row; identical bulk batch twice → second
  inserts 0 rows; two consecutive pipeline runs over the same mock day → 304 cells
  stay at 304 rows (`rows_inserted=0` on the second run).

## 7. J1 service integration

`src/ingestion/pipeline.py::IngestionPipeline.run(session, now)` implements exactly:

    Source -> normalize -> validate -> persistence -> ingestion-run status

1. create `ingestion_runs` row `RUNNING` (committed immediately → crash-auditable)
2. `IngestionService.ingest()` (fetch/normalize/validate — no DB)
3. one transaction: bulk-insert valid observations + close the run
   (`SUCCESS`/`PARTIAL`/`BLOCKED`/`FAILED`, counts + error preserved)

When the source is unreachable: the run is recorded **BLOCKED** with
`error_type=SourceUnavailableError`, the real error message preserved, and
**zero** observations inserted. No fallback to historical files occurs.

## 8. Mock behavior

- `MockObservationSource` remains gate-kept behind `LIVE_ALLOW_MOCK=1`
  (`allow_mock=True` on the pipeline/service).
- When explicitly enabled, mock runs persist through the SAME repository path with
  `source=mock-sim` and `run_metadata.source_is_mock=true` — never presented as real IMD data.
- Without `allow_mock`, the run is recorded `FAILED` (`error_type=ConfigurationError`)
  and zero observations are inserted (guard preserved).

## 9. Tests

- **Offline:** `tests/test_phase_j2_schema.py` — 23 passed (always run, no DB needed).
  Covers schema definitions (tables/columns/unique/check/indexes via SQLite + model
  metadata), repository pre-validation (negative/NaN/None rainfall, naive timestamps,
  missing fields, unknown cell), offline unique-constraint enforcement, run status
  mapping, and run lifecycle CRUD.
- **Live PostgreSQL:** `tests/test_phase_j2_db.py` — 21 passed (real DB, empty-→migrate-
  twice reproducibility; skipped entirely when the test DSN is unreachable). Covers live
  schema (including `timestamp with time zone`), single/bulk insert, retrieval by
  cell/time/latest, both idempotency paths, validation, DB CHECK enforcement, all run
  transitions (SUCCESS/FAILED/BLOCKED with counts + errors), and pipeline integration:
  IMD-unavailable → BLOCKED + zero observations + error preserved; mock path → SUCCESS +
  deterministic Persisted data; mock path idempotent across runs; mock guard → FAILED.

## 10. PostgreSQL connectivity status

**OPERATIONAL.** `DATABASE_URL` and `DATABASE_URL_TEST` both configured and reachable
(`ping` = True). Live migration executed, schema verified against the actual database,
and all 21 DB tests ran (not skipped) against PostgreSQL. This gate's required live
validation WAS actually executed.

## 11. Blocked items

- Real IMD live source remains **BLOCKED** at the data-availability layer (J1 finding:
  endpoint returns HTTP 200 with 0 bytes for year 2026). This is a J1 data-source
  condition, NOT a J2 database blocker; the pipeline handles it and records BLOCKED
  runs correctly (proven by the `IMD unavailable` integration test).
- J3+ (features, inference, API coupling) deliberately not implemented.

## 12. Scientific integrity confirmation

- No changes to `FREEZE_H.json`, frozen XGBoost revival/persistence models, climatology,
  training matrix, Phase H feature definitions, or historical labels.
- No training, no forecast computation, no Groq/LLM logic added.
- Missing/invalid rainfall is never converted to zero (rejected pre-insert, CHECK and
  message enforce it); timestamps stored timezone-aware; quality preserved.
- Only files touched for J2: `src/database/models.py`, `src/database/ingestion_repository.py`
  (new), `src/ingestion/pipeline.py` (new) + lazy exports in `src/ingestion/__init__.py`,
  migration `0002_live_ingestion.py` (new), two new test modules.

## 13. Regression results

- `python -m pytest tests/ -q` → **222 passed, 0 failed, 2 warnings** (same two
  pre-existing warnings: pytest return-not-none in `test_database.py`, numpy binary-size
  RuntimeWarning). Baseline 178 → 222 (+44 J2 tests). No Phase H / Phase I regressions.

## 14. Evaluator verdict

- Schema: verified live
- Migration: applied + downgrade/upgrade cycle proven
- Idempotency: proven (unique key + ON CONFLICT DO NOTHING)
- J1 integration + BLOCKED semantics: proven
- Mock gate: proven
- PostgreSQL connectivity: live and validated
- Regression: clean

**Verdict: J2 PASS**

---

## Files Changed

| File | Status |
|---|---|
| `src/database/models.py` | modified — `Observation`, `IngestionRun` models |
| `src/database/ingestion_repository.py` | **new** — repository layer |
| `src/ingestion/pipeline.py` | **new** — J1→DB integration pipeline |
| `src/ingestion/__init__.py` | modified — lazy pipeline exports |
| `database/migrations/versions/0002_live_ingestion.py` | **new** — Alembic migration |
| `tests/test_phase_j2_schema.py` | **new** — 23 offline tests |
| `tests/test_phase_j2_db.py` | **new** — 21 live PostgreSQL tests |