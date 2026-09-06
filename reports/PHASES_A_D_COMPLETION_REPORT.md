# PHASES A–D COMPLETION REPORT — SIH26086 Build Agent

**Status: COMPLETE — awaiting approval to proceed to Phase E (baselines).**
Generated 2026-09-06 · working tree snapshot at end of Phase D.

## 1. What was delivered

| Phase | Deliverable | Evidence |
| --- | --- | --- |
| A | Label engine + definition report | `src/labels/build_labels.py`, `reports/LABEL_DEFINITION_REPORT.md` |
| B | Feature pipeline (IMD/CHIRPS/NASA/ONI, train-only climatology) | `src/features/build_features.py`, `src/load.py` |
| C | Chronological training matrix + report | `src/build_matrix.py`, `data/processed/training_matrix.parquet`, `reports/TRAINING_MATRIX_REPORT.md` |
| D | Leakage audit (10 automated checks) + report | `src/leakage_audit.py`, `tests/test_leakage.py`, `reports/MODEL_LEAKAGE_AUDIT.md` |

## 2. Files created / modified

**Created:** `src/load.py`, `src/build_matrix.py`, `src/leakage_audit.py`, `tests/test_leakage.py`,
`src/labels/build_labels.py`, `src/labels/definitions.py`, `src/features/build_features.py`,
`reports/LABEL_DEFINITION_REPORT.md`, `reports/TRAINING_MATRIX_REPORT.md`,
`reports/MODEL_LEAKAGE_AUDIT.md`; `data/processed/training_matrix.parquet`,
`data/processed/label_daily.parquet`, `data/processed/label_events.parquet`,
`data/processed/cache/{chirps_cells,nasa_features}.parquet`.

**Modified:** `src/data_pipeline_utils.py` (+`PROCESSED` path); existing `src/load.py` preloaded in session.
No raw data re-downloaded, no checksums altered.

## 3. Commands run

```
python src/labels/build_labels.py          # labels (Phase A)
python src/build_matrix.py                 # matrix (Phase C)
python src/leakage_audit.py                # audit + report (Phase D), exit 0
python -m pytest tests/test_leakage.py -q  # 10 passed (1 benign numpy size warning)
```

## 4. Results

- **Domain**: 304 IMD 0.25° cells in TN/MH/KA pilot boxes; 3,040 cell-years.
- **Labels**: 2,981 onsets (98.1 %), 59 no-onset, 3,408 false-onset candidates,
  11,902 break runs, 6,487 dry-spell runs, 11,835 revivals. `insufficient_data` = 0.
  Example-driven validation incl. 2019 drought (6 stalled candidates, onset Sep-15) and a
  textbook false-onset → 14-day dry-spell → revival sequence.
- **Matrix**: 370,880 rows (JJAS days) × 63 cols; 47 numeric features
  (imd 24, chirps 5, nasa 16, oni 2, + doy/dseason); **0 NaN in features**.
  Splits train 259,616 / val 74,176 / test 37,088 (calendar-derived, never shuffled).
- **Leakage audit**: L‑1..L‑10 all PASS (future-rain checks, ONI release ≥45 d, window
  anchoring, TRAIN-only climatology, per-cell label independence, no dups, calendar split).

## 5. Notable mid-phase fixes (documented)

1. Pilot-cell filter removed 185 Cartesian "corner" cells outside actual boxes.
2. NASA CSV header-block parsing (comment='-' mis-detection) → `read_nasa_csv`; NASA
   feature values spot-verified against raw files.
3. **ONI season-month bug**: dict comprehension collapsed duplicate letters (J/F/M/A),
   shifting every season end by ~2 months → replaced with 3-consecutive-letter positional
   match; corrected matrix rebuilt (oni_1@2021-07-12 = −0.56 verified).
4. Dry-spell threshold aligned to documented 1.0 mm (was 0.5 mm in an early constant).
5. Removed duplicated context columns (`doy_x/dseason_y` etc.) caused by merge collisions.

## 6. Unresolved issues / caveats

1. **ERA5** still absent (no CDS key provided) → optional feature group; not blocking.
2. **Official GIS** (block/village) pending → `admin_mapping=PENDING_OFFICIAL_GIS` everywhere;
   grid-cell identifiers only, nothing fabricated.
3. Proxy thresholds in `src/labels/definitions.py` are `CALIBRATION_PENDING` until MoES
   checklists arrive; they are single-source constants, never edited inline.
4. 2024 (test) is a heavy-break year (break rate 0.428 vs 0.329 train) — expected, watched.
5. pytest warning: numpy binary-incompat warning from pandas/pyarrow stack (cosmetic).

## 7. Scientific assumptions (rolled into reports)

Wet=1 mm; onset = first JJAS day with 3-day sum ≥20 mm + 2-day sustain ≥2.5 mm, once per
cell-year, JJAS-only trailing window; break = ≥5 d <2.5 mm post-onset; revival = first ≥2.5 mm
post-break; dry spell = ≥7 d <1 mm post-onset; missing days count dry; >10 % missing →
label NaN. See LABEL_DEFINITION_REPORT (definitions.py is the single source).

## 8. Recommended next phase (upon approval)

**Phase E — baselines** in the mandated order: climatology → persistence → logistic regression
→ random forest → XGB/LGBM; per-target (onset/break/dry-spell/revival) with train configs
saved, reported on train/val/test separately, never tuned on 2024; then Phase F probabilistic
evaluation (Brier, calibration, ROC/PR-AUC, F1/P/R, confusion) vs climatology/persistence.
Gate: stop after E–G for review as specified.