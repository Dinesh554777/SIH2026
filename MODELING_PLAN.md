# MODELING_PLAN

**Project:** SIH26086 — Hyperlocal Monsoon Onset & Break Prediction
**Status:** Design document · no ML pipeline implemented yet

---

## 1. Modeling Philosophy

- **States are predicted; phases are classified.** We never predict a continuous rainfall field at 30 days. We classify state transitions and estimate probabilities.
- **Baseline-first, sophistication last.** Every target must first be solved by climatology and persistence baselines. ML earns its place only by beating them.
- **Honesty over accuracy.** "94% accuracy" is a danger sign (rare-event trap). We report calibration, skill vs baselines, and proper probability scores.
- **State-conditioning.** Each target is only defined/active in the correct monsoon state.
- **No LLM in forecasting.** Non-negotiable.

## 2. Model Hierarchy (per target, per horizon Λ)

| Tier | Model | Purpose |
| ---- | ----- | ------- |
| T0a | **Climatology** | historical event-frequency in calendar window at block |
| T0b | **Persistence** | current state continues to window end |
| T0c | Climatology + small ML (optional) | cheap strong reference |
| T1 | **Gradient boosting** (LightGBM/XGBoost) on feature set F | primary learned model |
| T2 | Sequence models (LSTM/temporal transformer) | **only if** justified (see §6) |

**Decision rule:** T2 is adopted only if, in nested cross-validation, it beats T1 by a meaningful margin and does so reproducibly; otherwise default to T1. A well-tuned GBM with lag/rolling features is the expected winning choice for this problem.

## 3. Target Modeling (per state)

### 3.1 Problem framing
Each target is a **binary classification** task per (block, issue_date, horizon):

| Target | Conditional on current_state |
| ------ | ---------------------------- |
| `onset` (1 = sustained onset within Λ days) | pre-onset |
| `false_onset` (1 = non-persistence follows trigger) | pre-onset |
| `break` (1 = break begins/persists within Λ days) | active |
| `revival` (1 = revival within Λ days) | break |
| `rainfall tercile` (multi-class 3) | any state |

**Event logic:** labels are built from the definitions in `DATA_DICTIONARY.md §2`, using only rainfall observed inside the window *after* issue date.

### 3.2 Conditional outputs
The state classifier assigns `current_state` at issue date. The engine returns only the active outputs for that state (others `N/A`). This prevents the nonsense case "P(onset) when monsoon already arrived."

## 4. Feature Set F (draft)

Selection via temporal cross-validation; no future data in features. Groups:

1. **Rainfall state:** lags 1–30d, rolling sums/means (7/14/21/30), rain-day counts, `cdd`, `cwd`, `rf_max1d`, anomaly vs climatology.
2. **Climate signals:** `nino34` (lagged), `dmi` (lagged), `mjo_phase`, `mjo_amp`, (MISO if obtainable). **Used as context; expected marginal effect at short lead.**
3. **Monsoon state:** `current_state`, `state_duration` — the single most informative set for break/persistence.
4. **Seasonality:** `doy`, `day_of_season`, climatological window anchors.
5. **Geography:** `elevation_m`, `land_use_class`, block climatological baseline.
6. **Near-term context (for 7–14d):** last 3–7 days of NWP/ERA5 anomaly fields if available.

**Feature hygiene rules:**
- Lag features must use `t-Λ` or earlier relative to issue date where horizon matters.
- No feature may be constructed from rainfall that occurs *inside* the evaluation window.
- Every feature has a versioned builder; features recomputed per fold to avoid leakage (rolling stats must not cross fold boundaries).

## 5. Data Leakage Prevention (Hard Rules)

1. **Strict temporal splits.** Train on years Y0..Yc, validate on Yc+1..Yc+v, test on the latest held-out seasons. **No random shuffling.**
2. **Rolling-origin evaluation.** For each fold, forecasts are issued from dates at horizon-distance before the validation window, so the window itself is never "seen."
3. **Feature recomputation per fold.** Rolling/lag features recomputed within the training domain only.
4. **Index/calibration only on train + validation folds.** Ground-truth labels of test years touch nothing until final evaluation.
5. **No normalization across full dataset** (standardization fitted on train only).
6. **State classifier labels** are derived from the same definitional pipeline as evaluation labels — the classifier cannot see future rainfall in features at issue date.
7. **Provenance per artifact** (DATASET → TIMESTAMP → FEATURES → MODEL VERSION) so leakage is auditable.

## 6. Model Selection Protocol (T2 Guard)

- If sequence models are attempted:
  - Same folds, same labels, same metric as T1.
  - Nested CV: inner for hyperparameters, outer for honest skill estimate.
  - Acceptance threshold: consistent validation metric improvement + robustness across seeds; otherwise rejected with the decision recorded (this is itself a defensible engineering/science artifact).

## 7. Decision Engine Thresholds (Rule Table — Draft)

| Scenario | Inputs | Decision |
| -------- | ------ | -------- |
| Pre-onset | P(onset) ≥ 0.7, P(false) ≤ 0.3, confidence high | **Sow** (rainfed, crop-aware) |
| Pre-onset | P(onset) mid, P(false) high | **Delay** sowing |
| Active | P(break) ≥ 0.6 | **Monitor**, prepare contingency |
| Active | P(break) high + irrigated | **Irrigate** planning / supplement |
| Break | P(revival) ≥ 0.6 | **Resume** activities / sow short-cycle |
| Any | Confidence < abstention threshold | **Wait for confirmation** (abstain) |

> Thresholds are placeholders (`[ASSUMPTION]`) to be:
> (a) justified via cost-of-error analysis (false positive vs false negative have unequal cost),
> (b) made crop/region-specific with agronomic sources.
> **The decision engine is rule-based; no model or LLM decides actions.**

## 8. Implementation Order (when approved)

1. Build label pipeline (definitions) + state classifier → verify on small sample.
2. Repro T0 baselines (climatology, persistence) across all targets/horizons.
3. T1 GBM per target; calibrate (isotonic/Platt on validation folds).
4. Compare vs baselines (see EVALUATION_PLAN) — record every number.
5. T2 only if justified.
6. Decision engine + explanation layer consuming calibrated JSON output.
7. Dashboards.

## 9. Known Model Risks

| Risk | Mitigation |
| ---- | ---------- |
| Rare events → accuracy illusion | Precision/recall, Brier, reliability-focused metrics |
| Calibration drift | Recalibration per fold + versioned models |
| State classifier errors cascade | Report classifier accuracy separately; evaluate targets conditional on true state too |
| Overfitting climate signals | Signals are few and lagged; expected to dominate only at long lead |