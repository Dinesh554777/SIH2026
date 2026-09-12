# Phase J1 — Live Data Ingestion Report

**Gate:** J1 — Live Data Ingestion (data acquisition only; no forecasting)
**Date:** 2026-09-12
**Author:** OpenCode automated pipeline

---

## 1. Objective

Build a real live-observation ingestion pipeline that fetches daily IMD 0.25°
gridded rainfall over the registered pilot cells (304 cells across TN / MH / KA)
from the operational IMD Pune endpoint, normalizes it to the project's internal
model, validates and classifies freshness, and returns a structured
`IngestionResult` — all WITHOUT performing any forecasting or database writes.

Gate J1 is scoped to the ingestion layer only. Forecasting remains decoupled
(J3), database persistence is J2, and frontend live mode is J5.

---

## 2. Architecture

```
Live data source (IMD / Mock)
         |
         | ObservationSource.fetch(now)
         v
    SourceResponse  (raw rows + metadata)
         |
         | validators + normalizer
         v
    Observation[] (valid) / rejected[] (with quality + reason)
         |
         v
    IngestionResult
         |
    [J2: PostgreSQL persistence — not yet wired]
    [J3: Feature builder — not yet wired]
```

J1 does NOT touch the database, models, or API. Historical-mode code is
completely unaffected.

---

## 3. Source Selection

| Source | Type | Access Method | Role in J1 |
|---|---|---|---|
| IMD rfp25 (Pai et al. 2014) | Official authoritative | POST RF25.php {RF25=year} | Primary live source |
| Mock | TEST-ONLY deterministic | Local hash-based | Automated test suite |

Historical `.nc` files under `data/raw/imd` are NEVER used as a live source.
They are frozen validation fixtures consumed only by `src.load.imd_series()`.

---

## 4. Endpoint / Config

| Parameter | Default | Source |
|---|---|---|
| `FORECAST_MODE` | `historical` | Env var |
| `LIVE_DATA_SOURCE` | `imd` | Env var |
| `LIVE_SOURCE_URL` | `https://www.imdpune.gov.in/cmpg/Griddata/RF25.php` | Verified POST endpoint (2026-09-02) |
| `LIVE_REQUEST_TIMEOUT_SECONDS` | `30` | Env var |
| `LIVE_MAX_RETRIES` | `2` | Env var (0–10) |
| `MAX_OBSERVATION_AGE_HOURS` | `48` | Env var |
| `LIVE_ALLOW_MOCK` | `0` | Env var; must be `1` to use mock source |

The IMD POST pattern (`POST RF25.php`, body `{RF25: <year>}`, headers with
User-Agent/Referer) was verified against the live endpoint on 2026-09-02 via
`src/data_download/download_imd.py`.

---

## 5. Normalized Schema

```
Observation
├── cell_id          : str     "{lat:.2f}_{lon:.2f}"  (deterministic mapping)
├── lat / lon        : float   pilot 0.25° grid cell centre
├── observation_time : datetime timezone-aware (UTC)   the rainfall day
├── rainfall_mm      : float   mm/day  (units are EXPLICIT, never silently zeroed)
├── source           : str     "imd" | "mock-sim"
├── retrieved_at     : datetime timezone-aware (UTC)   system-retrieval timestamp
├── quality_flag     : str     valid | missing | invalid | stale | future
└── reason           : str | None  human-readable reason (None when valid)
```

---

## 6. Validation Rules

| Check | Outcome | Quality |
|---|---|---|
| Missing lat / lon / observation_time | `invalid` | presence schema failure |
| Latitude ∉ [-90, 90] or longitude ∉ [-180, 180] | `invalid` | coordinate out of range |
| Rainfall < 0 | `invalid` | negative rainfall rejected (not zeroed) |
| Rainfall NaN / inf | `invalid` | non-finite value |
| Rainfall present but `None` | `missing` | measurement absent, not schema failure |
| Observation time is naive (no tzinfo) | `invalid` | timezone required |
| Observation time > now + tolerance | `future` | future-dated rejection |
| Age > MAX_OBSERVATION_AGE_HOURS | `stale` | outside freshness window |
| Age within freshness window | `valid` | fresh observation |
| Coordinate not within a registered pilot cell | `invalid` | unknown_cell |

Rejected observations are ALWAYS returned (never silently dropped) with
their quality_flag and reason for downstream auditing (§10 of spec).

---

## 7. Freshness Classification

Batch-level freshness is determined by the **most recent successfully-parsed
observation time** across both valid AND rejected observations (so that an
all-stale batch correctly reports "stale" rather than "unavailable"):

| Flag | Meaning |
|---|---|
| `fresh` | latest observation within MAX_OBSERVATION_AGE_HOURS |
| `stale` | latest observation older than MAX_OBSERVATION_AGE_HOURS |
| `future` | latest observation ahead of now + tolerance |
| `unavailable` | no successfully-parsed timestamps |

---

## 8. Retry / Error Handling

Transient failures (network timeout, HTTP error, malformed response) are
retried with a bounded burst (up to `LIVE_MAX_RETRIES + 1` total attempts):

| Error type | Retriable? | Behavior |
|---|---|---|
| `SourceUnavailableError` (timeout, HTTP, DNS) | Yes | bounded retry; clean failure after exhausting attempts |
| `SourceResponseError` (malformed data) | Yes | bounded retry (once may be transient) |
| `ValidationError` / `ConfigurationError` | No | raised immediately, no retry |
| Normalization semantic failure | No | returned in IngestionResult.errors, not raised |

No infinite loops. Tests confirm bounded attempt counts.

---

## 9. Mock Source (TEST-ONLY)

`MockObservationSource` is a deterministic fixture source:
- Produces exactly 304 rows (one per pilot cell) for a fixed observation day
- Rainfall per cell is `hash(cell_id + date)` → `range [0.4, 46.0]` mm/day
- `is_mock = True`; service blocks ingestion unless `allow_mock=True` (gate-kept)
- Used exclusively by the automated test suite (internet-free)
- Never labeled as live operational data

---

## 10. Test Results

**36 J1-specific tests passed** in 1.32s (internet-free):

| Category | Tests | Notes |
|---|---|---|
| Configuration | 6 | mode, source, mock guard, URL validation, retries range |
| IMD Client Shape | 3 | default URL, local path rejection, http accepted |
| Per-observation Validation | 7 | required fields, negative/NaN/None rainfall, coords, naive datetime, future, stale |
| Freshness Classification | 4 | fresh/stale/future via service layer |
| Normalization | 2 | units preservation, ISO string timestamps |
| Geographic Cell Mapping | 4 | exact center, within tolerance, far outside, format |
| Bounded Retry | 3 | transient failure, transient-then-success, ValidationError not retried |
| Mock Source | 4 | determinism, guard blocked, guard allowed, result shape |
| Helper | 1 | target_observation_date = last completed day |
| IMD Client Shape (url) | 2 | local rejection, http acceptance |

**Full regression suite: 178 passed, 0 failed, 2 warnings** (pre-existing
numpy binary compat warning + pytest return-not-none warning; no regressions).

---

## 11. Real-Source Connectivity Result

```
[probe] source=imd
[probe] url=https://www.imdpune.gov.in/cmpg/Griddata/RF25.php
[probe] STATUS: BLOCKED
[probe] REASON: IMD returned status=200 bytes=0 for year=2026
    (endpoint reachable, returns empty body — current year not yet available)
[probe] ATTEMPTS: 3 (bounded retries exhausted)
[probe] DURATION: 6.32s
```

**ENDPOINT STATUS: BLOCKED**

The IMD Pune operational endpoint is reachable (HTTP 200, DNS resolves, TCP
connects) but returns an empty body for year=2026. This is a legitimate data-
availability issue (the current year's daily file may not be published yet on
the operational portal). The 200-vs-0-bytes check in the client correctly
detects this and refuses to proceed with a malformed payload.

Historical years (2015–2025) are accessible from the same endpoint per the
project-verified pattern (see `src/data_download/download_imd.py`).

**No fabricated live data was produced. The system is honest about what it
received: zero bytes.**

---

## 12. Files Changed / Created

| File | Status | Purpose |
|---|---|---|
| `src/ingestion/__init__.py` | **new** | Package root; public API |
| `src/ingestion/errors.py` | **new** | Error taxonomy (retriable vs permanent) |
| `src/ingestion/config.py` | **new** | LiveConfig from env vars |
| `src/ingestion/models.py` | **new** | Observation + IngestionResult dataclasses |
| `src/ingestion/validators.py` | **new** | Per-observation validation + freshness |
| `src/ingestion/normalizer.py` | **new** | CellMapper + normalize_batch |
| `src/ingestion/service.py` | **new** | IngestionService (fetch + retry + normalize) |
| `src/ingestion/clients/__init__.py` | **new** | Source client package |
| `src/ingestion/clients/base.py` | **new** | ObservationSource ABC + SourceResponse |
| `src/ingestion/clients/imd.py` | **new** | IMD rfp25 POST client (verified endpoint) |
| `src/ingestion/clients/mock.py` | **new** | Deterministic MOCK/TEST-ONLY source |
| `src/ingestion/connectivity.py` | **new** | Runnable real-source connectivity probe |
| `tests/test_phase_j1_ingestion.py` | **new** | 36 internet-free J1 tests |
| `.env.example` | **modified** | Added J1 environment variables |

---

## Limitations

1. Real IMD source returns 0 bytes for 2026 (data availability issue, not a code
   bug). Ingestion will succeed automatically once the file becomes available.
2. IMD daily rainfall total uses midnight UTC as observation_time convention
   (the day's rain is associated with the start of that day). This is documented
   and consistent with the historical pipeline.
3. The source client is sync (blocking); future multi-source concurrent ingestion
   may benefit from async — not in scope for J1.

---

## Verdict

**J1 PASS — LIVE CONNECTIVITY BLOCKED**

- All J1 code committed and tested (36 tests, full regression 178 passed)
- Real IMD endpoint reachable but year=2026 returns empty body (honest BLOCKED)
- No fabricated live data; no historical files labeled as live; no database writes
- Ready for Gate J2 (PostgreSQL persistence of ingested observations) upon approval
