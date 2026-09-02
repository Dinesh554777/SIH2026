# E. Forecast Science

## E.1 The Forecast Horizon Hierarchy

```
       NOWCASTING        SHORT          MEDIUM        SUBSEASONAL       SEASONAL
        0–6 hrs         1–3 days       ~3–10 days      2–4 weeks         months
          │                │               │              │                │
          ▼                ▼               ▼              ▼                ▼
    SIH26086's neighbors → deterministic detail declines → large-scale slowly-varying signals
    (84/85)                                     become relatively more important
```

## E.2 The Predictability Wall ⭐

> **How much information about the future atmosphere actually contained in today's atmosphere?**

Skill falls with lead time:

```
Skill
100%   ██████████
       ████████
       ██████
       ████
       ██
       █
       └──────────────────────────
         1d   3d   7d   14d  30d    Lead time
```

*(Conceptual illustration, not numeric claims.)*

At longer lead times:
- Large-scale slowly-varying signals matter more.
- Local deterministic details become much less predictable.
- **This is exactly why SIH26086 needs probabilistic outputs.**

## E.3 Weather vs Climate vs Subseasonal (Know Cold)

| Concept | Example |
| ------- | ------- |
| Weather | Will it rain tomorrow? |
| Medium-range weather | Rainfall over next 5 days |
| **Subseasonal** | **Rainfall/monsoon behavior over next 1–4 weeks** ← SIH26086 |
| Seasonal climate | How will monsoon behave this season? |
| Climate | Long-term patterns over decades |

## E.4 S2S — Subseasonal-to-Seasonal Prediction

The "predictability gap" between weather (deterministic, days) and climate (statistical, seasons). SIH26086 is squarely in the **subseasonal** band. Sources of subseasonal predictability: MJO/MISO propagation, soil moisture, snow cover, ocean states.

## E.5 Probabilistic Prediction (The Mindset Shift)

**Bad output:** "Monsoon onset will occur on June 18."
**Good output:** "Probability of sustained onset during June 15–22: 72%."

```
Onset probability
██████████████░░░░ 72%      Confidence: Moderate–High
```

You are saying "based on available evidence, this outcome has this likelihood" — never "this definitely happens."

## E.6 Why Probability Is Especially Important for Farmers

| Scenario | Probability | Meaning |
| -------- | ----------- | ------- |
| A | Onset 90%, dry-spell 10% | Sowing conditions favorable |
| B | Onset 60%, dry-spell 70% | Sowing is risky — planting then losing rain = crop damage |

`Prediction → Risk → Decision` is more useful than `Prediction → Rainfall number`.

## E.7 Ensemble Forecasting

Multiple model runs (perturbed initial conditions) → distribution of outcomes → probability estimate from the ensemble spread. Ensembles are the standard way subseasonal skill is realized operationally. The ensemble **spread** is itself an uncertainty measure.

## E.8 Forecast Confidence (Not the Same as Probability)

```
ONSET PROBABILITY 72%
Confidence: MODERATE
Why?
• climate signals agree
• recent rainfall supports onset
• local historical pattern supports onset
• long-range uncertainty remains
```

Confidence bands: **High / Moderate / Low**. This matters because a wrong agricultural recommendation has real consequences.

## E.9 Why "95% Accuracy" Is Dangerous

If breaks occur ~10% of the time, a model that always says "no break" scores 90% accuracy while being useless. **Accuracy alone is misleading for rare events and for probabilities.**

## E.10 Key Forecast-Science Terms

- Lead time
- Forecast uncertainty / ensemble spread
- Probabilistic forecast
- Reliability / calibration (see G)
- Resolution (does the forecast sharpen correctly?)
- Skill score (vs. a reference — see G)

## E.11 Ready-to-Answer Questions

1. What is subseasonal prediction?
2. Why is 30-day prediction difficult?
3. Why probability instead of deterministic prediction?
4. What happens when confidence is low?