# SIH26086 — MVP Product Specification

Date: 2026-09-07 · Project: **Hyperlocal Monsoon Onset & Break Prediction System (probabilistic decision support)**

Status: **DRAFT FOR APPROVAL — documentation only, no implementation yet.**

---

## 1. Product statement

> **Probabilistic block/cell-level monsoon decision support that converts subseasonal
> rainfall signals into actionable agricultural guidance while explicitly representing
> uncertainty.**

The MVP answers, for a selected 0.25° grid cell (approximately 25 km × 25 km):

> "Given the current monsoon state and recent rainfall, what is the likely near-term
> rainfall regime at this location, how confident are we, and what agricultural action
> should the user consider?"

The product does **NOT** claim deterministic village-level weather prediction, and never
falsely implies that a grid cell is an official village/block boundary.

---

## 2. Primary user

**CHOICE: District/Block Agriculture Extension Officer (and the district Agriculture
Department office that supports them).**

Rationale:

- They make operational, repeated decisions with real stakes (advise sowing windows,
  irrigation pull-back, transplanting, fertilizer timing) and currently lack an
  uncertainty-aware subseasonal rainfall-regime signal for their area of responsibility.
- One officer represents many villages at once — a cell/block-level product is exactly
  their scale, and they can translate outputs into group advisories.
- They are professionally capable of understanding "probability + confidence" language,
  unlike a raw-farmer interface that demands near-certain language.
- They are reachable in a 36-hour demo context (e.g. a demo against Tamil Nadu/Maharashtra/
  Karnataka pilot cells is plausible) and are a credible SIH stakeholder per the MoES
  problem statement.

### User goals

| Item | Content |
| ---- | ------- |
| Goal | Deliver timely, uncertainty-aware monsoon regime guidance to the farms under their block |
| Decision | Whether to advise / hold off on: sowing preparation, actual sowing, irrigation, re-sowing, fertilizer application |
| Information currently lacking | A single, calibrated nowcast/near-term probability of onset / break / revival / dry-spell at their spatial scale with confidence |
| How the system helps | Frozen, validated models produce the 4 probabilities per cell from daily rainfall + context; a decision layer maps them to concrete advisory text |
| Why uncertainty matters | A "78% revival" is semantically different from "78%" being a yes/no fact; officers deciding farm operations on a false-certainty forecast cause real losses. The system's value IS its calibrated probabilities. |

## 3. Secondary users (separate, deferred)

| User | Need | MVP status |
| ---- | ---- | ---------- |
| Extension workers (field) | Same as officer, on mobile, more visual | Beneficiary via officer radio/print; direct UI deferred |
| Farmers | Personal location guidance in local language | Deferred; served indirectly through officer advisories |
| State/crisis management officials | District-level summarization of active breaks/dry spells | Deferred; aggregate endpoint is a later extension |

## 4. Core user journey

```
1. Officer selects location (map picker or search by cell / nearest district town)
2. System resolves the selection to the nearest 0.25° pilot cell (+ shows its grid identity)
3. System loads the latest rain observations for that cell (and neighbors) up to day t
4. Frozen models generate the four target probabilities (onset / break / revival / dry-spell)
5. System renders probabilities with a confidence category + uncertainty note
6. System translates the state into agricultural interpretation + suggested actions
7. Officer can expand "Why?" → key contributing features (e.g., rainfall acceleration,
   wet streaks, 7-day variability) and model provenance
8. Officer can inspect uncertainty + evidence (training years, sample sizes, calibration band)
```

Explicitly minimal: selection → forecast → guidance → why. No auth, no chat.

## 5. MVP output per location

### Monsoon status block
- Current rainfall state: last observed daily rainfall, 3/7/14-day sums
- Wet/dry regime indicator (based on training definitions: wet day ≥1 mm; trace ≥2.5 mm)
- Trend: rainfall acceleration (up/down) — the strongest revival feature (`th_accel`)

### Forecast signals block (four probability cards)
- Onset probability (P(onset day today))
- Break probability (P(active break day today))
- Revival probability (P(revival day today))  ← the ML-driven card
- Dry-spell probability (P(active dry-spell day today))

### Confidence
- Probability in %, a **communication band** (low / moderate / high / very high), and a
  small data note (n validation positives, model calibration ECE).
- Language rules enforced in UI copy:
  - ✅ "Revival probability: 78% — relatively high confidence"
  - ❌ "Rain will definitely occur"

### Decision support block
- One-line agricultural interpretation + suggested action (per table in the decision rules doc)
- Marked: "agronomic suggestion — requires expert validation"

---

## 6. Frozen modeling architecture (non-negotiable)

Exactly `data/processed/FREEZE_H.json`:

| Target | Frozen model | Inputs |
| ------ | ------------ | ------ |
| Onset | persistence (Markov P(y_t\|y_{t-1})) | previous-day onset state; dseason==1 → cell-dseason climatology |
| Break | persistence | previous-day break state; dseason==1 → climatology |
| Revival | **XGBoost + Group B (temporal)** | 64 features: 51 Group A + 13 `th_*`; XGB hyperparams in FREEZE_H |
| Dry spell | persistence | previous-day dry-spell state; dseason==1 → climatology |

Imputation (revival only): `SimpleImputer(median)` with train-fit medians frozen in
FREEZE_H.json for `th_rstd7`, `th_rstd14`, `sp_mean_lag1` — applied identically to live data.

Persistence parameters (from training 2015–2021):
| Target | p11 (stay active) | p01 (enter) |
| ------ | ----------------- | ----------- |
| onset | 0.0000 | 0.0082 |
| break | 0.9078 | 0.0475 |
| revival | 0.0000 | 0.0314 |
| dry-spell | 0.9165 | 0.0209 |

No LSTM/GRU/Transformer/CNN; no retraining; no new algorithms in the MVP.

---

## 7. Forecast horizon & operational timing assumption

- **Prediction target:** probability that a monsoon-state target is ACTIVE on day *t*
  at the selected cell (onset day / break-day / revival day / dry-spell day).
- **Operational assumption (explicit):** the forecast for day *t* is generated **after**
  day-*t* rainfall observations are available for the cell **and its neighbours**
  (spatial features use same-date neighbouring rainfall; temporal features include
  same-day rainfall; prediction-time availability was audited during Phase H).
- **Update frequency:** once per day, after the daily rainfall ingest (end-of-day t).
- **Observation cutoff:** day *t* (IMD grid deltas), lag-1 and lag-3 rain, trailing 3/7/14/30-day windows.
- **Forecast timestamp:** end-of-day *t*; responses carry the observation date explicitly.
- Horizon honesty: the system is a **real-time regime-assessment + near-term trend
  guidance** tool (state nowcast with subseasonal context), NOT a day-3/day-5 deterministic
  weather forecast. UI and docs must not imply days-ahead deterministic precision.