# J. Product

## J.1 What You Are Building

A **probabilistic monsoon-phase decision-support system** for block/village-scale agricultural decisions — **not** a weather app.

Competitive positioning:

> **"We transform subseasonal monsoon signals into block-level agricultural decisions while explicitly representing uncertainty."**

NOT: "we predict weather better than IMD."

## J.2 The Two Users

| User | Needs |
| ---- | ----- |
| **Farmer** | Plain-language answer to "should I sow this week?" + confidence + local language |
| **Extension officer / agriculture dept / FPO** | Block-level outlooks, risk summaries, evidence for advisories, monitoring |

Secondary users: district/block agriculture departments, irrigation planners, disaster-management authorities, rural finance/insurance.

## J.3 Where the LLM Fits (and Where It Doesn't)

**NOT** the forecasting brain. **Only** for:

- multilingual explanation
- conversational querying
- advisory wording

```
Scientific prediction model → Probability → Decision engine → Structured advice → LLM → explanation (Tamil/English/regional language)
```

Structured output flows to the LLM:

```json
{
  "onset_probability": 0.72,
  "dry_spell_probability": 0.65,
  "confidence": "moderate",
  "decision": "delay_sowing"
}
```

Example LLM wording:

> "Rainfall conditions show signs of onset, but there is still considerable risk of a dry spell. For rainfed farming, waiting for stronger confirmation may reduce risk."

This separation (ML predicts, LLM explains) is what makes the architecture credible.

## J.4 What the Farmer Receives

```
Onset probability:  48%
Persistent onset:   31%
14-day dry-spell:   67%
Recommendation:     Delay rainfed sowing by 7 days. Monitor rainfall confirmation.
```

Understood as a **decision + confidence + reason**, in local language.

## J.5 Demo Strategy ⭐ — Demo a Failure Case

Do NOT demo "here is our dashboard." Demo a **false onset** story:

- Day 0: rainfall observed → farmer thinks monsoon arrived.
- System: onset 48%, persistent onset 31%, 14-day dry-spell 67%.
- Recommendation: **delay rainfed sowing 7 days**.
- Then show the historical hindcast: **observed = false onset → dry spell → eventual revival**.

This creates a powerful judge moment and directly connects to the scientific story.

## J.6 Farmer Decision Scenarios (Reusable Demo Cases)

| Scenario | System behavior |
| -------- | --------------- |
| A. Early rain, weak persistence | Warn false-onset risk |
| B. Established monsoon, 10–14 day reduction likely | Flag break/dry-spell risk |
| C. Break probability falling | Flag possible revival |

## J.7 Localized Explainability

Give "why," not "SHAP = 0.31":

> **Why is the system expecting a possible break?**
> • Recent rainfall deficit
> • Historical pattern for this phase
> • Large-scale climate signal
> • Weak rainfall persistence
> **Confidence: Moderate**

## J.8 Product Features Queue (Understood, Not Yet Proposed for Development)

- Multilingual dashboard (farmer + officer views)
- Block/panchayat-level visualization
- Plain-language recommendations + confidence
- Alerts (sowing-window / dry-spell watch)
- Explanation & provenance per forecast
- **Explicit low-confidence / abstention state**

## J.9 Competitor / Alternative Comparison

| Approach | Strength | Weakness | Your opportunity |
| -------- | -------- | -------- | ---------------- |
| Traditional regional forecast | Established | Coarse spatial scale | Downscale to decision units |
| Weather apps | Easy to use | Short/medium-range focus | Monsoon phase + decisions |
| Raw ML rainfall model | Learns nonlinear patterns | Overfits, not interpretable | Benchmark + uncertainty + explainability |
| Static agricultural advisory | Actionable | Doesn't respond to forecast | Forecast-driven recommendations |
| **Your system** | Prediction + uncertainty + advisory | Scientifically challenging | Decision-support layer |