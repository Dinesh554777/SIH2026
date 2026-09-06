# TRAINING MATRIX REPORT — SIH26086

**Phase C · training matrix** · generated 2026-09-06
Artifact: `data/processed/training_matrix.parquet` (370,880 rows × 63 cols, ~85 MB)
Rebuild: `python src/build_matrix.py`
Providers: IMD 0.25° (labels+IMD features), CHIRPS v3.0 0.05° (5 features), NASA POWER daily (16), NOAA ONI v6 (2); see `DATA_SOURCES.md`.

## 1. Sampling design (temporal non-anticipation by construction)

| Aspect | Design |
| --- | --- |
| Spatial unit | IMD 0.25° cell (`cell_id`) — 304 cells inside union of TN/MH/KA pilot boxes (`src/load.py:select_pilot_cells`) |
| Time unit | calendar day, **JJAS only** (122 d/y) — the window where onset/break/dry-spell/revival are defined |
| Sample (row) | one (cell, date) pair → 304 × 1220 = **370,880** rows |
| Feature time-anchoring | every predictor at date T uses observations **≤ T** (end-of-day T allowed; advisory fires post-day-close) |
| Climatology | fit **exclusively** on TRAIN (2015–2021) — see Phase D check L-6 |
| ONI | only seasons released ≥45 d before T (lag ≥ 1 season) — L-4 |
| Admin mapping | `admin_mapping=PENDING_OFFICIAL_GIS`; `bbox_guess` is an unverified box label only (no fabricated district/block) |

## 2. Splits (never shuffled)

| Split | Calendar | Rows | % | Cell-years |
| --- | --- | --- | --- | --- |
| train | 2015-01-01 .. 2021-12-31 (JJAS samples) | 259,616 | 70.0 % | 7 × 304 |
| val | 2022-01-01 .. 2023-12-31 | 74,176 | 20.0 % | 2 × 304 |
| test | 2024-01-01 .. 2024-12-31 | 37,088 | 10.0 % | 1 × 304 |

Date span: 2015-06-01 .. 2024-09-30. All cells present in every split (no cell drain).

## 3. Targets & class balance (per split, mean = positive rate)

| Target | train | val | test | note |
| --- | --- | --- | --- | --- |
| `onset_active` (day-of-onset) | 0.0080 | 0.0080 | 0.0081 | ~1 per 122-day season |
| `break_active` (in break run) | 0.3286 | 0.3232 | 0.4282 | 2024 = heavy-break year |
| `dry_spell_active` (in ag. dry spell) | 0.1935 | 0.2038 | 0.2642 | |
| `revival_day` (revival day only) | 0.0302 | 0.0290 | 0.0375 | |

Severe class imbalance for `onset_active` and `revival_day` (≤3 % positive) → Phase E
must use class-weighted loss/threshold calibration and report Brier/ROC-AUC/PR-AUC, and
Phase F baselines (climatology/climatological-persistence) as the comparison floor.

**Persistence floor (train):** P(break_t | break_{t−1}) = 0.905 vs climatological base 0.329.
Any Phase-E forecast model must beat the persistence signal to add information.

## 4. Feature inventory (47 numeric)

| Group | Count | Features |
| --- | --- | --- |
| `imd_*` | 24 | `rain_t`, `rain_lag1/3`, `sum3/7/14/30`, `wet1`, `wet3/7/14/30`, `dry3/7/14/30`, `max3`, `days_since_wet` (cap 60), `consec_dry` (cap 60), `cum_jjas`, `anom_t`, `anom7/14/30` (vs train-only climatology) |
| `chirps_*` | 5 | `rain` (0.05°→cell mean, verified == manual bbox mean), `lag1`, `sum7`, `sum14`, `wet7` |
| `nasa_*` | 16 | 8 params (T2M, T2MDEW, T2M_MAX, T2M_MIN, RH2M, PS, WS10M, WS10M_MAX) × {`_t`, `_a7`}; nearest-grid-point (verified vs raw CSV) |
| `oni_*` | 2 | `oni_1`, `oni_2` (last/previous released ONI; released = season end + 45 d) |
| context | 2 | `doy`, `dseason` (kept strict — no cross-cell leakage) |

Δt sensitivity: lag/aggregation windows {3,7,14,30} days selected to cover the
synoptic-to-subseasonal skill range of the baseline tree models in Phase E.

## 5. Data completeness

- Missing values in features: **0** (`NaN cells: 0`). IMD pilot cells are validated 0–0.8 %
  missing; missing IMD days are NaN in labels only (cell-year trigger `insufficient_data`);
  CHIRPS has no -9999 sentinel in the pilot files (0.0 for ocean/void pixels, all land within
  the window is valid); NASA masked (-999) rows removed; ONI fully populated for all samples
  (release ≥45 d before JJAS window start holds for 2015-06-01 onward).
- `insufficient_data` rows: 0 (no cell-year exceeded the 10 % missing tolerance).

## 6. Provenance & verification

- IMD `ind_<year>_rfp25.nc` v1 (file+sha256 in `data/checksums.csv`); labels per
  `reports/LABEL_DEFINITION_REPORT.md`.
- CHIRPS v3.0 pilot extracts (unified bbox, VERIFIED 3653/3653 d); cell means re-computed
  manually over the 0.05° footprint → exact match (13.08092 …).
- NASA POWER daily CSVs (header-block skip fixed in `src/load.py:read_nasa_csv`);
  T2M at (10.0, 76.25, DOY=152) = 27.46 both in features and raw file.
- ONI v6 (918 rows 1950–2026); as-of mapping strictly ≤ released seasons.
- Checksums and download logs audited: `reports/CHECKSUM_REPORT.md`.

## 7. Known limitations

1. Pilot-domain, not official-GIS resolution; district/block mapping is explicitly
   `PENDING_OFFICIAL_GIS` (see `DATASET_LIMITATIONS.md`).
2. ERA5 atmospheric predictors excluded by design until CDS credentials land
   (optional feature group E in the Phase-G ablation).
3. Labels are the operational proxy (reports/LABEL_DEFINITION_REPORT.md §6) —
   thresholds centralized in `src/labels/definitions.py`, `CALIBRATION_PENDING`.
4. 0 NaN is partly by construction (conservative run semantics); a missing IMD day counts as
   "dry" for break/dry-spell run continuity (documented, never silent).