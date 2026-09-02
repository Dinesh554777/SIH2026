# SYSTEM_ARCHITECTURE

**Project:** SIH26086 — Hyperlocal Monsoon Onset & Break Prediction (Block/Village Scale)
**Status:** Design document · implementation blocked until review

---

## 1. Architectural Principles

1. **Prediction and decision are separated.** ML/statistics do prediction; a rule-based engine does agricultural decisions; an LLM (if used) only explains.
2. **Probabilistic outputs everywhere.** No deterministic "temperature/rainfall" claims at subseasonal lead.
3. **Verification is part of the pipeline** (hindcast → calibration → feedback), not a post-hoc report.
4. **Abstention is a first-class output.**
5. **State-conditioning:** all phase probabilities are defined relative to the block's current monsoon state.

## 2. Pipeline Overview

```
┌───────────────────────────────────────────┐
│                DATA SOURCES               │
│                                            │
│  IMD gridded rainfall (ground truth)      │
│  ERA5 / reanalysis (coarse predictors)    │
│  NASA POWER / alternatives (backup)       │
│  Climate indices (ENSO, IOD, MJO/MISO)    │
│  Geography / boundaries / elevation       │
└─────────────────────┬─────────────────────┘
                      ▼
┌───────────────────────────────────────────┐
│           DATA INGESTION (ETL)            │
│  Download / API / file → standard schema  │
│  Normalised units, UTC dates, grid/block  │
│  mapping, dataset version recorded        │
└─────────────────────┬─────────────────────┘
                      ▼
┌───────────────────────────────────────────┐
│        DATA QUALITY ENGINE                │
│  Missing values • outliers • date/spatial │
│  alignment • bias vs IMD rainfall noted   │
└─────────────────────┬─────────────────────┘
                      ▼
┌───────────────────────────────────────────┐
│        FEATURE ENGINEERING                │
│  Rainfall lags & rolling stats            │
│  Rain-day / consecutive wet+dry counts    │
│  Climate signal features (Niño3.4, DMI,   │
│    RMM/MISO phase)                        │
│  Day-of-season / climatological windows   │
│  Elevation & geographic context           │
└─────────────────────┬─────────────────────┘
                      ▼
┌───────────────────────────────────────────┐
│         MONSOON STATE CLASSIFIER          │
│  current_state ∈ {pre-onset, active,      │
│  break, revival} per block                │
│  (drives which outputs are active/N/A)    │
└─────────────────────┬─────────────────────┘
                      ▼
┌───────────────────────────────────────────┐
│        FORECASTING ENGINE                 │
│  Horizon models: Λ ∈ {7, 14, 21, 30}     │
│  Tier 0 baselines: climatology,           │
│     persistence, climatology+ML           │
│  Tier 1 ML: gradient boosting (baseline+  │
│     features)                             │
│  Tier 2 (justified only): temporal/LSTM   │
│  All tiers output calibrated probabilities│
└─────────────────────┬─────────────────────┘
                      ▼
┌───────────────────────────────────────────┐
│     PROBABILISTIC OUTPUT LAYER            │
│  P(onset) P(break) P(revival)             │
│  tercile rainfall / expected rain (≤14d)  │
│  confidence per output & horizon          │
└─────────────────────┬─────────────────────┘
                      ▼
┌───────────────────────────────────────────┐
│   BLOCK-LEVEL STATISTICAL DOWNSCALING     │
│  coarse prob → block prob via local       │
│  climatology relationships                │
│  Village = derived risk shading only      │
└─────────────────────┬─────────────────────┘
                      ▼
┌───────────────────────────────────────────┐
│    VERIFICATION & CALIBRATION (loop)      │
│  hindcast vs observed labels              │
│  reliability / Brier / skill vs baseline  │
│  recalibration (isotonic/Platt)           │
│  feeds back into forecasting engine       │
└─────────────────────┬─────────────────────┘
                      ▼
┌───────────────────────────────────────────┐
│        AGRICULTURAL DECISION ENGINE       │
│  rule-based: Sow / Delay / Irrigate /     │
│  Monitor / Wait(abstain)                  │
│  input: outputs + crop + irrigation +     │
│  sowing window context                    │
└─────────────────────┬─────────────────────┘
                      ▼
┌───────────────────────────────────────────┐
│      EXPLAINABILITY & PROVENANCE          │
│  reasons (rainfall deficit, climatology,  │
│  climate signals, persistence)           │
│  data lineage / model version / timestamp │
└──────┬──────────────────────┬─────────────┘
       ▼                      ▼
Farmer dashboard        Officer dashboard
 (multilingual,          (block outlooks, risk
  decision-first)        summaries, evidence)
```

## 3. Component Specifications

### 3.1 Data Ingestion
- **Inputs:** the datasets in `DATA_SOURCES.md`.
- **Outputs:** versioned, aligned tabular/geo tables with uniform schema (see `DATA_DICTIONARY.md`).
- Records source, timestamp, processing step for every table (data lineage from the start).

### 3.2 Data Quality Engine
- Imputation policy per field (e.g., gap-fill only where observation density permits; otherwise mark missing).
- Outlier flagging (physically impossible values excluded/flagged).
- **Date alignment:** daily grid at a single timezone (IST), holiday/leap handled.
- **Spatial alignment:** coarser fields (ERA5, climate indices) matched to blocks via nearest/weighted interpolation, documented as a method assumption.

### 3.3 Feature Engineering
Full list and types in `DATA_DICTIONARY.md`. Key groups:
- **Rainfall:** lags (1–30d), rolling sums/means (7/14/21/30), rain-day counts, consecutive dry/wet days, anomaly vs climatology.
- **Climate signals:** Niño 3.4, DMI (IOD), RMM/MISO phase + amplitude, lag-shifted where sensible.
- **Seasonality:** day-of-year, climatological phase windows.
- **Geography:** elevation, block climatological anchors, land-use class.
- **State features** (critical): current monsoon state label + its persistence duration.

### 3.4 Monsoon State Classifier
- A deterministic/rule-based or simple learned classifier assigning `current_state` per block per day, using onset/break/revival definitions from `PROJECT_REQUIREMENTS.md (§4)`.
- Outputs drive which prediction targets are active (state-conditional matrix).
- Classifier is **verified against the same labels** used for evaluation (no double standards).

### 3.5 Forecasting Engine
- **Tier 0 baselines** (always produced, always reported):
  - **Climatology:** historical frequency of the event in that calendar window at that block.
  - **Persistence:** assume current state continues to end of window.
  - (Optionally) climatology + a small ML model as a cheap strong reference.
- **Tier 1:** gradient boosting models (LightGBM/XGBoost) trained on features per horizon, per target, state-conditioned. Probabilities calibrated.
- **Tier 2:** temporal/sequence models (e.g., LSTM/temporal transformer) considered **only if** Tier 1 is beaten **after** proper validation and at justified compute cost. Default: skip. Guard clause: nested CV skill must exceed Tier 1.

### 3.6 Probabilistic Output Layer
- All probabilities within [0,1], calibrated (see §3.8).
- Confidence levels derived from (a) calibration reliability in the relevant bin, (b) model agreement/spread, (c) signal consensus. Output format:

```json
{
  "block_id": "b7201",
  "issue_date": "2026-06-15",
  "horizon_days": 14,
  "current_state": "active",
  "outputs": {
    "p_break": 0.65,
    "p_persistence": 0.35
  },
  "rainfall_tercile": {"below": 0.4, "near": 0.35, "above": 0.25},
  "confidence": {"overall": "moderate", "p_break": 0.8},
  "abstain": false,
  "decision": "monitor"
}
```

### 3.7 Block-Level Statistical Downscaling
- Coarse probabilistic forecasts + local climatology → block-level probability via statistical relationships.
- **Honesty rule:** village shown as derived shading; never deterministic village rainfall claims.
- Method + caveats documented; baseline for downscaling = "no downscaling" (district/coarse directly).

### 3.8 Verification & Calibration (Feedback Loop)
- After each hindcast window: reliability diagram, Brier score, ROC-AUC, skill vs climatology & persistence.
- Probabilities **recalibrated** (e.g., isotonic regression on the validation folds) before deployment per version.
- Loop writes results back into the model registry; model version bumps only when verified.

### 3.9 Agricultural Decision Engine
- **Rule-based only** (no ML, no LLM).
- Inputs: outputs + crop type + irrigation availability + sowing window + risk posture.
- Outputs: Sow / Delay / Irrigate / Monitor / Wait-for-confirmation (abstain).
- Awaiting the threshold table (see `MODELING_PLAN.md §7`) — thresholds documented and region/crop-specific.

### 3.10 Explainability & Provenance
- Explanation = short plain-language list of contributing factors (from feature attribution at the *decision-support level*, not black-box raw SHAP numbers alone).
- Data lineage: dataset → timestamp → processing → features → model version → prediction → recommendation.

### 3.11 Dashboards
- **Farmer:** decision-first, local language, probabilities as bars, confidence badge, "wait" state prominent when applicable.
- **Officer:** block-level map view, outlooks per horizon, verification stats, hindcast evidence.

## 4. Where the LLM Fits (and Where It Does Not)

```
Forecasting engine → probabilities → decision engine → structured advice
                                                                ▼
                                                     LLM (multilingual explanation,
                                                     conversational querying ONLY)
```

Structured decision JSON is produced without an LLM. The LLM renders plain-language text in English/regional languages. **The LLM never computes a probability, never chooses a decision, never touches features.**

## 5. Operational-Readiness Layer (Design Only)

Prototype = research system. Documented as "operationally extensible," with stubs noted for: live ingestion, monitoring, model versioning, alert management, forecast verification, audit logs, human oversight. Not implemented at hackathon scope unless time permits.

## 6. Technology Neutral (Deferred)

No stack decision yet. Priorities if/when implemented: reproducibility (versioned data + seeds), a single model registry, and a UI that renders the JSON above losslessly.