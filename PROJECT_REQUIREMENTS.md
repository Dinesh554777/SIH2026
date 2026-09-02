# PROJECT_REQUIREMENTS

**Project:** SIH26086 — Hyperlocal Monsoon Onset & Break Prediction System (Block/Village Scale)
**Organization:** Ministry of Earth Sciences (MoES) · SIH 2026
**Document status:** Design/research · No ML pipeline yet

---

## 1. Purpose

Build a **scientifically defensible, probabilistic monsoon-phase decision-support platform** that estimates the probability of monsoon phase transitions (onset / break / revival) at block scale over subseasonal horizons (7–30 days), quantifies uncertainty, validates against historical observations, and translates results into actionable agricultural recommendations.

**Explicitly NOT:**
- NOT deterministic village-level weather prediction.
- NOT a weather app.
- NOT "Dataset → LSTM → Dashboard."
- NOT a claim that we predict weather better than IMD.

## 2. Non-Negotiable Principles

| # | Principle | Consequence |
| - | --------- | ----------- |
| P1 | Probability over certainty | All phase outputs are probabilities + confidence, never single dates/amounts presented as facts |
| P2 | Uncertainty is represented, never hidden | Every forecast carries a confidence level; the system can abstain |
| P3 | Documented assumptions | All scientific definitions are written as explicit assumptions with source basis, not invented silently |
| P4 | Validation over demo | Hindcasting + comparison vs climatology/persistence are core deliverables |
| P5 | No data leakage | Time-respecting splits; features at time t use only data ≤ t |
| P6 | ML predicts, LLM explains | Forecasting never delegated to an LLM; LLM only for multilingual explanation/advisory wording |
| P7 | Decision-support, not autonomous advice | Agricultural recommendations are rule-based and framed as advisory input, with an abstention state |

## 3. Prediction Targets

Primary probabilistic targets, **state-conditional** (each target only meaningful in the correct monsoon state):

| Target | State it applies to | Meaning |
| ------ | ------------------- | ------- |
| P(onset) | Pre-onset | Probability that **sustained** monsoon onset is established within the forecast window |
| P(false onset) | Pre-onset | Probability that observed initial rainfall is NOT sustained onset (dry-spell risk) |
| P(break) | Active | Probability that a break / dry spell begins or persists within the forecast window |
| P(revival) | Break | Probability that rainfall activity recovers to active within the forecast window |
| P(persistence) | Active | Probability current active state continues (seen as 1 − P(break) at short lead) |
| Expected rainfall | Any | Probabilistic tercile / anomaly category, plus expected mm **only at 7–14 day lead** with spread |

**State-conditional outputs:** the `current_state` classifier determines which outputs are *active* and which are *N/A* per block (see MODELING_PLAN §Model A).

## 4. Scientific Definitions (Recorded as Assumptions)

### 4.1 Onset (assumption ON-1)
- Onset = establishment of a **sustained** rainfall regime at block scale, defined as:
  - Rainfall ≥ **onset threshold** (to be calibrated per block from historical quantiles, default working value documented at calibration time), AND
  - Persistence criterion met (e.g., ≥ N rainy days within a rolling M-day window, default N to be calibrated from block climatology), AND
  - Subsequent dry spell of not more than D consecutive dry days within the following window (protects against false onset).
- **Source basis:** adaptation of IMD operational onset concepts (regional onset over Kerala, normal 1 June ± ~7 days) **downscaled to block level**; local threshold values are working assumptions pending calibration.
- **Open decision (assumption ON-2):** distinguish "regional onset date" (from IMD/operational products) vs "block-level onset" — block-level onset is our target; regional onset is an input feature.

### 4.2 Break (assumption BR-1)
- A break/dry spell = period of ≥ **K consecutive days** (default to be calibrated: working value 5–7 days) with **daily rainfall below a threshold** (working default below block-specific normal-day rainfall quantile) during the established monsoon season.
- **Source basis:** literature convention for Indian monsoon breaks (≥3–5 consecutive days of suppressed rainfall); exact values are **recorded assumptions pending block-level calibration**, never arbitrary.

### 4.3 Revival (assumption RV-1)
- Revival = return from break state to active state, defined as rainfall ≥ threshold for ≥ J days within a rolling window (mirror of onset persistence criterion).
- **Source basis:** mirror of onset persistence logic; values recorded as assumptions pending calibration.

### 4.4 False Onset (assumption FO-1)
- False onset = onset criterion met (or rainfall spike observed) **followed by failure to persist**, i.e., dry spell exceeding D consecutive dry days within the post-onset window, without established monsoon continuation.
- **This is the centrepiece use case.** The system reports onset confidence AND dry-spell risk rather than a binary "monsoon arrived."

> **Policy:** every numeric threshold above must be (a) documented in DATA_DICTIONARY as an assumption, (b) calibrated per-block from historical climatology, or replaced with a sourced value. No magic numbers without a recorded rationale.

## 5. Prediction Horizons

| Horizon | Meaning | Expected uncertainty posture |
| ------- | ------- | ---------------------------- |
| 7 days | Near-term phase probability | Moderate–High confidence possible |
| 14 days | Subseasonal short leg | Moderate |
| 21 days | Subseasonal mid leg | Low–Moderate |
| 30 days | Subseasonal long leg | Structurally Low |

Rules:
- Every probability is **defined against an explicit window**: `P(event during next Λ days)` (episodic). Cumulative "by day X" forms are derived only where clearly labeled.
- Each horizon produces its own output vector; the system never blends horizons into a single "answer."
- Confidence is **per-output and per-horizon**; below-threshold confidence triggers abstention.

## 6. Spatial Resolution

- **Primary demonstration unit: Block** (and/or grid cell of the underlying rainfall product mapped to block geography).
- Village-level is shown as **derived risk shading** from block probabilities, explicitly labeled as uncertainty-blurred — no deterministic village rainfall claims.
- Downscaling method: **statistical** (coarse predictors → block local relationships), never manufactured local truth from coarse data alone.

## 7. Input Variables (Summary — full detail in DATA_DICTIONARY)

| Group | Variables |
| ----- | --------- |
| Rainfall (historical + current) | Daily rainfall (IMD gridded as ground truth), rolling sums/means, rain-day counts, consecutive wet/dry days |
| Reanalysis / NWP fields | ERA5 (or equivalent): temperature, pressure, humidity, wind (used as coarse predictors / context, not claims of local truth) |
| Climate signals | ENSO (Niño 3.4), IOD (DMI), MJO/MISO (RMM phase/amplitude or equivalent), SST fields |
| Monsoon state | Current state label (pre-onset / active / break / revival), state persistence, day-of-season climatological window |
| Geographic context | Block boundaries, elevation, land use, local climatology anchors |

## 8. Output Variables (Summary)

Per block, per horizon Λ ∈ {7,14,21,30}:

| Output | Type |
| ------ | ---- |
| P(onset) / P(false onset) | probability, state-conditional |
| P(break) / P(break onset or persistence) | probability, state-conditional |
| P(revival) / P(prolonged break) | probability, state-conditional |
| Expected rainfall | tercile probabilities + anomaly category; expected mm + spread only at ≤14d |
| Confidence | High / Moderate / Low, per output and per horizon |
| Decision | rule-based: Sow / Delay / Irrigate / Monitor / Wait-for-confirmation (abstain) |
| Explanation | plain-language reasons + data lineage (who/what/which model version) |

## 9. Constraints & Scope Boundaries

- Prototype is a **research/hackathon system**, framed as "an operationally extensible decision-support architecture" — not an operational meteorological system.
- No real-time government data commitment; live ingestion is out of scope unless a stable public API is confirmed (see DATA_SOURCES).
- Advisory layer is agnostic to "who is authorized" — it is decision-support; final crop-specific recommendations are rule-based and region/crop-aware, referencing standard agronomic guidance, not invented by the model.

## 10. Deliverables This Design Phase

1. PROJECT_REQUIREMENTS.md (this file)
2. SYSTEM_ARCHITECTURE.md
3. DATA_DICTIONARY.md
4. MODELING_PLAN.md
5. EVALUATION_PLAN.md
6. DATA_SOURCES.md

ML pipeline implementation is **not allowed to begin** until these documents are approved.

## 11. Risks (Top 5)

| Risk | Severity |
| ---- | -------- |
| Downscaling to village without village ground truth | Critical — mitigated by honest block-level claims |
| 30-day skill claims without hindcast proof | High — mitigated by baseline comparison |
| Magic-number onset/break thresholds | High — mitigated by documented+calibrated assumptions |
| Data leakage from future features | Critical — mitigated by strict temporal splits |
| LLM-as-forecaster temptation | High — mitigated by architectural separation (P6) |