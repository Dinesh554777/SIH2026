# SIH26086 — MVP System Architecture

Date: 2026-09-07 · Status: **DRAFT FOR APPROVAL**

## Principles

- **Evidence-backed simplicity**: most of the "AI" is persistence. Only revival uses a tree model.
- **Model serving over infrastructure**: precompute everything that can be precomputed; keep a thin inference path.
- **Frozen contract**: no retraining; the model layer only loads artifacts, never fits.

## Top-level diagram

```text
                 DATA SOURCES
                      |
       +--------------+--------------+
       |              |              |
    IMD(grid)      CHIRPS         NASA/ONI
       |              |              |
       +--------------+--------------+
                      |
               Ingestion + Validation        (daily, batch)
                      |
               Feature Pipeline             (re-deploys Phase H builders)
                      |
             Phase H Frozen Features
                      |
                Model Layer                 (loads frozen artifacts only)
          +-----------+-----------+----------+
          |           |           |          |
     Persistence Persistence Persistence  XGBoost(B)
          |           |           |          |
       Onset       Break      DrySpell    Revival
          |           |           |          |
          +-----------+-----------+----------+
                      |
             Probability Layer
                      |
           Decision-Support Engine         (rules, translated to text)
                      |
          +-----------+-----------+-----------+
          |           |           |           |
       Forecast     Advisory    Explainability  Provenance/Confidence
      endpoints    endpoints       (why.)       (calibration, caveats)
```

## Components (with hosting decision for a 36-hour MVP)

| Component | Role | MVP mode |
| --------- | ---- | -------- |
| Data sources | IMD 0.25° gridded daily rainfall (ground truth), CHIRPS (cross-check), NASA POWER (temp/humidity/wind), NOAA ONI (ENSO, lag≥45 d guard) | Pre-ingested research datasets on disk; live ingest stubbed/simulated for demo |
| Cell registry | 304 pilot cells (lat/lon, id, bbox-based region label) | Static JSON/parquet served read-only |
| Feature pipeline | Reuses `src/modeling/phase_h/features.py` builders (causal, train-only climatology) | Batch function; deterministic |
| Model layer | Loads frozen `models/phase_h/B/revival/*.joblib` (XGB, scaler, imputer) + frozen persistence params; no fit | Load at startup, in-memory |
| Probability layer | Produces the 4 probabilities + communication band | Pure function |
| Decision-support engine | Rules table → interpretation + action (+ optional LLM summarization) | Pure function; LLM optional |
| API | Thin REST layer (FastAPI) exposing ~3 endpoints | Container/process |
| UI | Single-page dashboard (no auth) | Static assets + API calls |
| Provenance store | Records model id, freeze hash, feature opt-out, calibration band | Side JSON / API envelope |

## Data flow (offline vs live)

```text
Raw Data            → Validation         → Feature Engineering → Frozen Model
   ↓                      ↓                      ↓                     ↓
 offline/batch        offline/batch         batch/precompute       in-memory load
 ---------------------------------------------------------------------------
Probability → Calibration/Confidence → Decision Rules → User Advisory
     ↓                ↓                     ↓                ↓
  real-time         real-time            real-time        real-time
```

Precompute strategy for 36 hours:
- **Offline**: label tables, climatologies, persistence params, imputer medians, model
  artifacts — all already exist in `data/processed` + `models/`.
- **Batch**: rebuild a `latest_obs.parquet` per cell from the research matrix (or a
  simulated "today" payload).
- **Real-time**: forecast request → build 64-feature row from current cell + neighbours →
  run frozen models → return envelope.
- No database required; a small state file or in-memory cell registry suffices.

## How the current repository maps to this

| Repo path | Role in MVP |
| --------- | ----------- |
| `src/modeling/phase_h/features.py` | canonical H1–H4 builders (spatial needs neighbour map: `build_neighbor_map`) |
| `src/modeling/phase_h/modeling.py` | `group_features()`, imputation medians, frozen artifact loading |
| `models/phase_h/B/revival/` | frozen XGBoost model + scaler + imputer + CONFIG.json |
| `data/processed/phase_h_matrix.parquet` | historical train/val/test for provenance + demo scenarios |
| `data/processed/FREEZE_H.json` | the contract (model ids, hyperparams, imputation, periods) |
| `data/processed/predictions/baseline_predictions.parquet` | persistence probabilities for any real date (incl. 2024) |
| `src/labels/definitions.py` | exact threshold meanings (wet day ≥1, trace ≥2.5, break ≥5 dry days, etc.) |

## Missing-data strategy (documented, not built yet)

- Spatially-missing neighbour rain → drop that neighbour from the aggregate when computing
  `sp_*` (already NaN-safe via `nanmean`), fall back to fewer neighbours.
- Structural boundary NaNs (`th_rstd7`, `th_rstd14`, `sp_mean_lag1` at season start) →
  train-frozen medians from FREEZE_H.
- >10% of JJAS missing for a cell-year → label unavailable (per definitions); forecast UI
  shows "insufficient data" rather than a number.

## Scaling note

Pipeline is embarrassingly parallel per cell and per target; 304 cells is trivial. Moving
to full India would reuse the same serving path with larger registries and scheduled ingest.