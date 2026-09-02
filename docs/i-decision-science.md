# I. Decision Science — From Probability to Action

> The forecast is not the product. The decision is the product.

## I.1 Decision Thresholds

Probability alone isn't enough. "Onset = 75%" — should the farmer sow? Depends on:

```
Probability
    + Crop
    + Risk tolerance
    + Sowing window
    + Irrigation availability
            ▼
    Decision threshold
            ▼
    Recommendation
```

A rainfed farmer may need stronger evidence than someone with irrigation. This is **risk-aware decision support**.

## I.2 Cost of a Wrong Prediction (Two Different Mistakes)

| Error | System says | Reality | Consequence |
| ----- | ----------- | ------- | ----------- |
| **False positive** | Safe to sow | Dry spell occurs | Crop loss |
| **False negative** | Delay sowing | Rainfall favorable | Missed sowing opportunity |

The two errors have **unequal economic cost**. Decision thresholds can be set to reflect which error hurts more.

```
Prediction → Probability → Economic/agricultural consequence → Decision
```

## I.3 Abstention — The "Don't Know" State ⭐

Most student systems always answer. A better system can say:

> "Insufficient confidence to issue a strong recommendation."

```
Onset probability: 54%   Break probability: 51%   Signals: conflicting
                    ▼
              ⚠ LOW CONFIDENCE
Recommendation: Wait for additional confirmation.
```

This is realistic and shows scientific maturity.

## I.4 Confidence Bands

- **High** — signals agree, strong historical support.
- **Moderate** — partial agreement / mixed evidence.
- **Low** — conflicting signals → abstain from strong recommendations.

## I.5 Forecast Provenance & Explainability

When the system says "dry-spell probability 68%", the user should get "why":

```
Forecast
│
├── Recent rainfall (deficit/surplus)
├── Historical climatology
├── ENSO
├── IOD
├── MJO
├── Regional atmospheric state
└── Model uncertainty
```

Plain-language explanation ≠ SHAP values. E.g.:

> "The probability increased primarily because recent rainfall is below the historical pattern and the large-scale indicators provide limited support for sustained rainfall."

## I.6 Data Lineage (For Operational Readiness)

```
Dataset → Timestamp → Processing → Features → Model version → Prediction → Recommendation
```

Traceability matters if the system is ever considered for operational use.

## I.7 Operational vs Research System — Be Honest

| Research prototype | Operational system would need |
| ------------------ | ------------- |
| Historical hindcast → prediction → advisory | Live ingestion, monitoring, model updates, missing-data handling, versioning, alert mgmt, forecast verification, audit logs, human oversight |

Position: **"We demonstrate an operationally extensible decision-support architecture using historical/live-accessible data."**

## I.8 The Four Innovation Layers (Ranked by Value)

1. **Farmer Decision Engine (⭐⭐⭐)** — forecast + crop situation → decision. The differentiator.
2. **Confidence-Aware Forecasting (⭐)** — "Onset probability 72%" with High/Moderate/Low confidence, not "Onset date: June 18."
3. **False-Onset Detector (⭐)** — onset confidence + dry-spell risk instead of binary "monsoon arrived."
4. **Localized Explainability (⭐)** — "why" in plain language, not feature-importance numbers.

## I.9 Core Decision-Support Answer Format

```
Onset probability:     72%
Dry-spell probability: 18%
Confidence:            Moderate–High
Decision:              Favorable sowing window (for rainfed, given crop X)
Explanation:           [plain language reasons — see I.5]
```

And the low-confidence variant: 54% / 51% / signals conflicting → ⚠ LOW CONFIDENCE → **Wait for confirmation.**

## I.10 The Uncomfortable Truth

> **"Why should we believe your model?"**
> Bad answer: "Because our LSTM achieved 94% accuracy."
> Good answer: "We do not claim deterministic village-level weather prediction. We estimate probabilistic risk using large-scale climate signals and local historical behavior, benchmarked against climatology and persistence. The advisory layer explicitly communicates uncertainty."