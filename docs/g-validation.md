# G. Validation & Hindcasting ⭐

> This is where most student teams lose points. Validation makes the system scientifically defensible instead of a demo.

## G.1 Ground Truth

The observed outcome your prediction is compared against.

```
Prediction            Observation
Break risk = 75%  →   Break occurred   (good hit)
Break risk = 20%  →   Break didn't occur
```

Ground truth questions to answer before coding:
1. What is your ground-truth dataset?
2. What is your spatial resolution?
3. What is your temporal resolution?
4. How many historical years do you have?
5. How will you handle missing observations?
6. How will you prevent data leakage?

## G.2 Hindcasting / Backtesting

Pretend you are standing in the past:

- Take historical data.
- On e.g. **June 1, 2018**, use ONLY information available at that time.
- Generate the forecast → compare to what actually happened.
- Repeat for 2015, 2016, ..., 2025.

**This gives you historical evidence without waiting for future seasons.** It is the single most persuasive validation artifact for a climate problem.

Strong statement:

> "We evaluated historical forecasts across multiple monsoon seasons and compared our probabilistic system against climatology and persistence baselines."

## G.3 Baselines — Your Reference Points

A number (e.g., 72% skill) means nothing without a reference.

### Climatology
Historical expectation: "This location historically has a 40% probability of a dry spell during this phase."
Your model says 43% → barely useful. Your model says 75%, correctly → real skill.

### Persistence
"Assume today's monsoon state continues" (active → active). A powerful, hard-to-beat simple baseline.

> **Model should beat both.** Judges may ask "does your model actually beat climatology?" — have the answer.

```
MODEL forecast probability
        ▼
Compare vs. historical expectation (climatology) and persistence
        ▼
Skill = information added beyond the baselines
```

## G.4 Time-Series Validation Traps

- **Data leakage:** using future info to predict the past; validate that all features at time t use only data ≤ t.
- **Random train/test split is wrong for time series.** Use temporal splits (train on 2000–2017, test on 2018–2025, etc.).
- **Multiple seasons:** "how many seasons did you validate on?" — have a concrete number.
- Proper approach: temporal cross-validation / rolling-origin evaluation.

## G.5 Probabilistic Metrics (Understand WHY Each Exists)

| Metric | Why it exists |
| ------ | ------------- |
| **Brier Score** | Mean squared error of probabilistic forecasts for binary events; scores calibration+resolution together |
| **Reliability / Calibration** | Does "70% predicted" actually happen ~70% of the time? |
| **ROC-AUC** | Ranking ability — does the forecast order cases correctly? |
| **Precision / Recall** | Useful for rare events (breaks/false onsets); avoids the "always predict no-break = 90% accuracy" trap |
| **Skill score vs. climatology** | Is the system better than the reference, normalized? |

## G.6 Calibration — Explained Simply

```
Predicted probability    Actual observed frequency
       20%                        ≈ 20%
       40%                        ≈ 40%
       60%                        ≈ 60%
       80%                        ≈ 80%
```

If true, the forecasts are **well calibrated**. This means more than claiming high accuracy — it means the stated probabilities mean what they say.

## G.7 Uncertainty Is a Feature, Not a Weakness

Student project: "our model predicts the answer."
Scientific system: "our model estimates likelihoods and communicates uncertainty."

Then: **Confidence: Low** is *responsible forecasting*, not failure.

## G.8 The Failure Cases to Study (Do This Early)

Research what happens when:
- rainfall station data is missing
- satellite observations are unavailable
- climate signals disagree
- model confidence is low
- extreme rainfall occurs
- local rainfall differs from regional conditions
- forecast is wrong
- onset occurs earlier/later than expected

Your system needs a **"don't know / low-confidence" state** (see I.3).