# DATA_DICTIONARY

**Project:** SIH26086 — Hyperlocal Monsoon Onset & Break Prediction
**Status:** Design document · All thresholds/definitions pending documented as assumptions; values marked `[ASSUMPTION]` must be calibrated per-block or replaced with sourced values.

---

## Conventions

- **Temporal:** daily resolution, timezone UTC+05:30 (IST); all joins on `(block_id, date)`.
- **Spatial unit:** block (primary). Downscaled support unit: grid cell of base rainfall product (~0.25° IMD grid).
- **Units:** rainfall in mm/day, temperature °C, pressure hPa, humidity %, wind m/s.
- Every table carries source + version + ingest timestamp (lineage).

---

## 1. Input Variables

### 1.1 Rainfall (Historical + Current) — Ground-Truth Anchor

| Field | Type | Description | Domain | Notes |
| ----- | ---- | ----------- | ------ | ----- |
| `rf_daily_mm` | float | Daily accumulated rainfall | ≥ 0 | IMD gridded rainfall primary source |
| `rf_anomaly` | float | Deviation from climatological daily mean | ℝ | vs block climatology |
| `rf_roll7/14/21/30` | float | Rolling sums (7/14/21/30-day) | ≥ 0 | windows in days |
| `rf_roll_mean7/14` | float | Rolling means | ≥ 0 | intensity proxy |
| `rain_days_n` | int | Count of wet days in trailing window | ≥ 0 | wet day: `rf_daily_mm ≥ 2.5` `[ASSUMPTION]` |
| `cdd` | int | Consecutive dry days (spell length) | ≥ 0 | dry day: `rf_daily_mm < 2.5` `[ASSUMPTION]` |
| `cwd` | int | Consecutive wet days | ≥ 0 | current spell |
| `rf_max1d` | float | Max single-day rainfall in trailing 7d | ≥ 0 | intensity spike flag |

### 1.2 Reanalysis / Coarse Atmospheric Fields (ERA5 or Equivalent)

| Field | Type | Description | Domain |
| ----- | ---- | ----------- | ------ |
| `t2m_mean` | float | 2-m air temperature (block mean) | K→°C |
| `t2m_anom` | float | temperature anomaly | ℝ |
| `mslp` | float | mean sea-level pressure | hPa |
| `sp` | float | surface pressure | hPa |
| `q2m` | float | 2-m specific humidity | kg/kg |
| `rh_mean` | float | relative humidity (if derived) | % |
| `u10`,`v10` | float | 10-m wind components | m/s |
| `ttl_precip` | float | model precipitation (ERA5) | mm/day — **context, NOT ground truth** |

> Coarse fields are matched to blocks via nearest-cell/weighted interpolation (method recorded as `[ASSUMPTION] SP-ALIGN-1`). ERA5 is a **predictor**, never validated against, never claimed as local truth.

### 1.3 Climate Signals (Large-Scale Drivers)

| Field | Type | Description | Source index |
| ----- | ---- | ----------- | ------------ |
| `nino34` | float | ENSO SST index | Niño 3.4 region |
| `dmi` | float | IOD dipole mode index | Indian Ocean SST gradient |
| `mjo_phase` | int | MJO phase 1–8 | RMM (or equivalent) |
| `mjo_amp` | float | MJO amplitude | RMM |
| `miso_phase` | int | MISO active/break phase | MISO index (Indian monsoon) |
| `sst_indian` | float | Regional Indian Ocean SST (optional) | extended |

**Handling notes:** indices are *context*, not predictors of local rainfall totals. Lag-shifts applied explicitly, documented in modeling plan. Missing MJO/RMM data → flag, do not silently fill.

### 1.4 Geography / Static Context

| Field | Type | Description |
| ----- | ---- | ----------- |
| `block_id` | str | Official block identifier |
| `lat`,`lon` | float | Block centroid |
| `elevation_m` | float | Mean elevation |
| `land_use_class` | cat | Cropland / plantation / etc. |
| `dist_to_sat` | float | Distance to nearest rainfall station/grid (data-reliability proxy) |

### 1.5 Derived / Label Variables

| Field | Type | Description | Notes |
| ----- | ---- | ----------- | ------ |
| `day_of_season` | int | Days since 1 June | calendar anchor |
| `doy` | int | Day of year | |
| `clim_rf` | float | Climatological daily mean at (block, doy) | from full history |
| `current_state` | cat | pre-onset / active / break / revival | from state classifier §3.4 |
| `state_duration` | int | Continuous days in current state | |
| `kharif_window_open` | bool | Whether within nominal sowing window | crop-aware, per region |

---

## 2. Prediction Targets / Label Definitions

Each target is **binary** (1 = event occurs within the window) built from rainfall + state definitions in `PROJECT_REQUIREMENTS.md §4`. Labels are computed per (block, issue_date, horizon) using **only** information available by the label definition (i.e., the observed window after issue date).

| Target | Definition (and associated `[ASSUMPTION]`) |
| ------ | ------------------------------------------ |
| `obs_onset` | 1 if sustained onset established within window per ON-1 |
| `obs_false_onset` | 1 if onset criterion met then persistence fails within the post-onset window (FO-1) |
| `obs_break` | 1 if break/dry-spell criterion BR-1 triggered within window |
| `obs_revival` | 1 if revival criterion RV-1 observed within window |
| `obs_tercile` | cat: below/near/above relative to block climatological terciles of the window rainfall total |

---

## 3. Output Variables

Per (block_id, issue_date, horizon Λ):

| Output | Type | Range | Definition |
| ------ | ---- | ----- | ---------- |
| `p_onset` | prob | [0,1] | P(sustained onset within window), active in pre-onset state |
| `p_false_onset` | prob | [0,1] | P(non-persistence) estimate for emerging onset |
| `p_break` | prob | [0,1] | P(break begins or persists within window) |
| `p_revival` | prob | [0,1] | P(revival within window) |
| `p_persistence` | prob | [0,1] | P(active state continues) = derived 1−P(break) at short lead |
| `p_tercile_below/near/above` | prob | [0,1] sum=1 | rainfall tercile probabilities |
| `rain_expect_mm` | float+spread | ≥0 | **Only at Λ ≤ 14d**; reported with uncertainty band |
| `confidence_*` | cat | High/Mod/Low | per output + per horizon, from calibration reliability + spread |
| `abstain` | bool | | true when confidence below abstention threshold `[ASSUMPTION] CONF-1` |
| `decision` | cat | sow/delay/irrigate/monitor/wait | rule-based, from decision engine |
| `explanation` | text | | plain language reasons + lineage |

---

## 4. Threshold / Definition Parameters Registry

All hard-coded scientific values live here, each tagged with status `[ASSUMPTION]`, `[CALIBRATED]`, or `[SOURCED]`:

| Param | Default working value | Status | Purpose |
| ----- | --------------------- | ------ | ------- |
| `wet_day_rf` | 2.5 mm `[ASSUMPTION]` | assumption | wet-day definition |
| `dry_day_rf` | 2.5 mm `[ASSUMPTION]` | assumption | dry-day definition |
| `onset_ref` | ≥ threshold (per-block*) `[ASSUMPTION]` | assumption→calibrate | onset rainfall trigger |
| `onset_persist_days` | N within M-day window* | assumption→calibrate | onset persistence |
| `max_cdd_after_onset` | D days* | assumption→calibrate | false-onset guard |
| `break_cdd_min` | K days (5–7)* | assumption→calibrate | break spell length |
| `break_rf_thresh` | per-block `[ASSUMPTION]` | assumption | break day threshold |
| `revival_persist_days` | J days* | assumption→calibrate | revival persistence |
| `abstain_conf_thresh` | TBD | assumption | confidence floor to act |

\* Calibrated from block historical climatology (e.g., quantiles) — values recorded post-calibration; the *method* is the contract, not the number.

---

## 5. Provenance Schema (Every Artifact)

```
dataset_name, source, version, resolution, ingested_at, processing_steps[],
block_mapping_version, feature_build_version, model_version
```

Required for every table, feature set, model, and prediction by the time the pipeline is executed.