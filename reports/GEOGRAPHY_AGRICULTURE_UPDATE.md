# Geography & Agricultural Update Report

**Gate:** Product-layer pivot — official administrative geography over the scientific grid
**Previous:** J2 PASS (PostgreSQL live persistence); J3 (live feature engineering) on hold pending full prompt
**Date:** 2026-09-12
**Author:** OpenCode automated pipeline

---

## 1. Why this changed

The scientific grid is a fixed 0.25°-resolution matrix (304 cells across Tamil Nadu /
Cauvery Delta). Agricultural decisions are made at administrative units — state,
**district**, **block** (the primary extension-decision unit), and **village**. The product
layer now exposes an official administrative hierarchy layered over the scientific grid,
so decision support can address "the Rajavoor block of Thanjavur district" while the
forecasting science remains cell-based. The mapping is derived explicitly from geometry
intersection — never guessed, never fabricated.

## 2. Pilot region

- **Tamil Nadu / Cauvery Delta** (the same region the frozen scientific grid covers).
- Formal hierarchy: State → District → Block → Village.
- **Block** is the primary agricultural decision unit; mapping exists for all levels.

## 3. Scientific grid resolution

- 0.25° x 0.25° cells, 304 cells, `cell_id` = `"{lat:.2f}_{lon:.2f}"`.
- The `cells` table (Phase I-B / scientific) is **untouched**. `seed_cells` reserves by
  leaving `cells.state = NULL` (nullable, kept transparent) — no administrative value is
  written into the scientific table.
- New product tables (`states`, `districts`, `blocks`, `villages`,
  `geography_grid_mapping`) live alongside, linked to the scientific grid only through
  the mapping table's FK to `cells.cell_id`.

## 4. Mapping method

- **Area-weighted intersection** (`map_grid_to_admin`, `area_weighted_intersection`) is the
  only method used for authoritative boundaries: a grid cell's fraction toward an
  administrative unit equals the shared polygon-area / cell-area.
- `centroid_only` exists in constants but is never used unless explicitly justified
  (no current use).
- Mapping is stored explicitly (`geography_grid_mapping` rows hold
  `intersection_fraction`, `intersection_area_deg2`, `cell_area_deg2`, method, source,
  version) — deterministic and reproducible, not recomputed on every read.
- Grid-cell coverage is conserved: every cell gets fractions summing to 1.0 within its
  valid fraction (handling WGS84 degree-area distortion), verified by the mapping test.

## 5. Authoritative GIS sources

A source is only accepted when it lands as a validated ready-bundle under
`data/geography/ready/` with a matching `source.json` manifest
(`dataset_name`, `provider`, `version`, `crs` = EPSG:4326/WGS84, `url`). Everything else
is refused:

> **GIS import STOPPED.** The repository contains no authoritative administrative
> boundary files. Section 15 of the directive requires refusing GIS import when
> authoritative data is unavailable — so administrative levels report **unavailable**
> rather than being invented, and the existing scientific grid keeps working untouched.

Candidate authoritative sources for the pilot (documented, not yet downloaded):
- Tamil Nadu State Land Use/Land Cover & Census 2011 administrative boundaries
  (Survey of India / open government data portals) — polygon per district/block.
- Data.gov.in district/block boundary layers (EPSG:4326) with versioned releases.
- NASADEM/geospatial datasets for elevation context (metadata only; not boundaries).

When any authoritative bundle is dropped into `data/geography/sources/`, validated, and
promoted to `ready/`, a new import run will populate the DB tables and mapping rows.

## 6. Agriculture metadata

- `agricultural_metadata` (JSON, nullable) lives on `blocks` and `villages`.
- Populated **only from authoritative data** (e.g. parcel/policy source with a versioned
  record). Unknown or blank fields fail loud (`load_agriculture_profile`) — they are never
  synthesized.
- With no authoritative source present, agriculture reports **unavailable**.

## 7. Product implications

- Consumers (future J5/J6 API) query administrative units and receive the mapped set of
  grid cells + area fractions; no inference layer changes.
- Availability semantics are explicit: `available`, `unavailable`, or per-level counts via
  `geography_availability(...)`. An empty inventory is `unavailable`, never an empty
  guess.
- The grid remains the 304-cell scientific layer; the product hierarchy is a view over it.

## 8. India expansion architecture

- Table schema is hierarchy-generic: each level references a string `{level}_id`
  (e.g. `state_id`, `district_id`, ...) with a parent FK. Adding additional administrative
  depth (e.g., sub-district) is a new migration + one line in `HIERARCHY` /
  `GEOGRAPHY_TYPES`.
- `geography_grid_mapping` already holds `geography_type`; any new level plugs in without
  schema churn.
- Cell coverage is independent of admin geography: 304 grid cells map onto any number of
  administrative units per region; mapping can be extended region-by-region without
  touching frozen science.

## 9. Database changes (migration 0003)

- `database/migrations/versions/0003_geography.py` — reversible; down `0002`.
- Adds `states`, `districts`, `blocks`, `villages`, `geography_grid_mapping`.
- `geography_grid_mapping`: FK `grid_cell_id → cells.cell_id` (RESTRICT),
  CHECK `geography_type IN (state,district,block,village)`,
  CHECK `intersection_fraction` 0..1, unique `(grid_cell_id, geography_type, geography_id)`;
  degenerate mapping (self-fraction 1.0, 0.0) rejected by tests/code.

## 10. Repository / integrity

- `src/database/geography_repository.py`: idempotent upserts, `assert_mapping_references`
  (mapped geo + cell must exist) runs before insert — integrity enforced in code and by DB.
- `count_geography`, `count_mappings`, `list_geography`, `children`, `mappings_for_geo/cell`,
  `geography_availability` provide read paths; nothing here mutates scientific tables.

## 11. API prep

- No J4 API endpoints were implemented (out of scope for this gate). The registry +
  repository abstraction is the API-ready seam: `GeographyRegistry` in memory and
  `geography_repository` as persistence. The future API layer calls these.

## 12. Live compatibility

- Live DB proven: `alembic upgrade head` reaches `0003`; downgrade to `0002` removes only
  geography tables and leaves `cells`/`forecasts`/`observations`/`ingestion_runs` intact
  (`test_downgrade_to_0002_removes_geography_only`).
- `cells` preserved: `seed_cells` writes 304 rows with `state = NULL`; no scientific
  columns altered.

## 13. Tests

- `tests/test_geography.py` — 17 offline tests: availability semantics, hierarchy
  validation, mapping conservation (WGS84-correct fractions), area-weighted determinism,
  read-only registry, no-fabrication refusal, agriculture profile fail-loud.
- `tests/test_geography_db.py` — 11 live PostgreSQL tests: schema/migration head 0003,
  upsert idempotency, hierarchy persistence, mapping reference checks, fraction CHECK,
  end-to-end import from a synthetic validated bundle, blocked-import without a bundle,
  downgrade/upgrade cycle.
- Full regression: **250 passed, 0 failed** (28 geography tests added on top of the 222
  J0–J2 baseline; same 2 pre-existing warnings).

## 14. Scientific integrity

- `FREEZE_H.json` and the frozen revival/persistence XGBoost models, climatology, training
  matrix, Phase H feature definitions, and historical labels are byte-identical (digests
  unchanged in tests).
- No training, no forecast computation, no inference changes.
- No boundary names, centroids, or agricultural figures were fabricated; the GIS import
  STOP is intentional and documented.

## 15. Verdict

- Domain: registered
- Registry availability: correct (unavailable until an authoritative bundle exists)
- DB migration 0003: applied live, reversible
- Mapping: area-weighted, stored, deterministic
- Scientific layer: 304 cells untouched
- Regression: clean (250 passed)

**Status: GEOGRAPHY DOMAIN + PERSISTENCE COMPLETE — awaiting authoritative GIS data or
directive for next gate (J3 resume / J5 seeding / data procurement).**

---

## Files Changed

| File | Status |
|---|---|
| `src/geography/` (constants, entities, sources, loader, mapper, agriculture, registry, `__init__`) | **new** — domain layer |
| `src/database/models.py` | modified — State/District/Block/Village/GeographyGridMapping |
| `database/migrations/versions/0003_geography.py` | **new** — migration 0003 |
| `src/database/geography_repository.py` | **new** — repository + integrity |
| `tests/test_geography.py` | **new** — 17 offline tests |
| `tests/test_geography_db.py` | **new** — 11 live PostgreSQL tests |
| `requirements.txt` | modified — added `shapely>=2.0` (mapper runtime dep) |
| `reports/GEOGRAPHY_AGRICULTURE_UPDATE.md` | **new** — this report |