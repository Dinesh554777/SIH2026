# EVALUATION_PLAN

**Project:** SIH26086 — Hyperlocal Monsoon Onset & Break Prediction
**Status:** Design document

---

## 1. Evaluation Philosophy

The deliverable is not "a model that scores high." It is **evidence that the model adds information beyond what is already known** (climatology, persistence) **and that its probabilities mean what they say** (calibration), demonstrated over **multiple historical monsoon seasons** via honest hindcasting.

**Never report "95% accuracy" without context.** Rare-event accuracy is a trap (always predicting "no break" scores ~90% on a 10%-frequency event while being useless).

## 2. Experimental Protocol (Hindcast / Backtest)

1. **Data:** full period split by year.
2. **Splits (temporal, rolling-origin):**
   - Train: earliest years (e.g., 2001–2014 `[ASSUMPTION]`, depends on data availability).
   - Validate: next block (e.g., 2015–2019) for calibration & development decisions.
   - Test (held out): most recent seasons (e.g., 2020–2025) — **touched only once at the end**.
3. **Issue setup:** on each issue date `d`, issue forecasts for Λ ∈ {7,14,21,30} days, per block, per target, using only information available at `d`.
4. **Rolling-origin:** iterate issue dates across the season (Jun–Sep) each year.
5. **Verification after each fold:** recompute metrics, recalibrate on validation folds, record before/after.

**Reporting rule:** results must be reported **per horizon**, **per target**, **per state**, and **versus the baselines**, not as a single headline number.

## 3. Ground Truth & Labels

- **Ground truth source:** IMD gridded daily rainfall (block-matched), the agreed reference for observation.
- **Labels:** built by a single definitional pipeline (DATA_DICTIONARY §2), versioned, shared by training and evaluation (no double standards).
- **Missing data:** labeled "unknown/not verifiable" where observations are insufficient (never silently excluded).

## 4. Metrics (Why Each One Is Used)

### 4.1 Probability-calibration metrics
| Metric | Purpose | Note |
| ------ | ------- | ---- |
| **Reliability diagram** | Visual: does 70% predicted ⇒ ~70% observed? | primary diagnostic |
| **Brier score** | MSE of probabilistic forecasts; joint calibration+resolution | compare vs climatology Brier (`BSS`) |
| **Brier skill score vs climatology** | Information added beyond reference | **headline skill metric** |
| **Calibration error (e.g., integrated calibration index)** | Numeric calibration summary | per bin |

### 4.2 Discrimination / ranking metrics
| Metric | Purpose |
| ------ | ------- |
| **ROC-AUC** | Can the forecast order events correctly? |
| **Precision / Recall, F1** | Rare events (break, false onset): detection usefulness |
| **Reliability vs resolution trade-off** | reported jointly (diagram) |

### 4.3 Decision metrics (context)
| Metric | Purpose |
| ------ | ------- |
| **Cost-weighted error / expected loss** | False-positive (crop loss) vs false-negative (missed sowing) unequal costs → threshold choice |
| **Abstention rate** | Fraction of cases where low confidence → wait; reported to show honesty is quantified |
| **Hit rate of the decision under the cost function** | Does the recommendation reduce expected loss vs climatology-driven decisions? |

### 4.4 Tercile rainfall forecast
- 3-category: **Ranked probability score (RPS)** vs climatological terciles + reliability per category.

## 5. Baselines (Required Comparisons)

| Baseline | Definition | Why |
| -------- | ---------- | --- |
| **Climatology** | Historical event frequency for (block, calendar window) | the "know-nothing" reference |
| **Persistence** | Current state persists to window end | the "do-nothing" reference |
| **Climatology + ML** (optional T0c) | Simple ML on climatology features | cheap strong reference |
| **Official/operational** (if available) | IMD/regional; qualitative only | ecosystem check, not primary |

**Skill scores are always computed relative to climatology and persistence** — separately. Claim "better than climatology" only where the number (with uncertainty) shows it.

## 6. Downscaling Validation

- Compare block-level forecasts vs:
  1. **No-downscaling reference** (same model applied at district/coarse level) — is the block adjustment adding value?
  2. Observed block rainfall (labels) — where sufficient observations exist.
- Report skill at coarse level AND at block level; do not silently claim block gains.
- Downgrade claims where village-level observations are absent (honest limitation).

## 7. Model Selection Evidence (Required Outputs)

| Artifact | Description |
| -------- | ----------- |
| Metric table | per target × horizon × state: BSS, Brier, AUC, P/R, reliability err |
| Baseline comparisons | skill vs climatology AND persistence |
| Reliability diagrams | per target/horizon (before/after calibration) |
| Calibration curve | numeric + visual |
| T2 vs T1 decision log | if sequence models considered: rejection/acceptance record with numbers |
| Season-by-season table | show variance; avoid "one lucky season" claims |
| Hindcast case studies | false-onset event (e.g., 2018-type `[ASSUMPTION]` example) showing the system flagging dry-spell risk → observed dry spell |

## 8. The "Why Believe Us" Statement (Defensible)

> "We do not claim deterministic village-level weather prediction. We estimate probabilistic risk using large-scale climate signals and local historical behavior, benchmarked against climatology and persistence across multiple monsoon seasons, with calibration demonstrated per output and per horizon. The advisory layer communicates uncertainty and can abstain."

## 9. Anti-Patterns Documented (Do Not Do)

- Accuracy-only reporting (rare-event trap).
- Random train/test split (leakage).
- Single-season validation.
- Claiming village skill without village observations.
- Hiding low-confidence cases.
- Reporting climatology as your model's skill.