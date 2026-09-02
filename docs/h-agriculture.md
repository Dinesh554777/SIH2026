# H. Agriculture

> The final output must be useful for farming. Learn the agricultural context so the recommendation layer is agronomically justified — not LLM-generated farming advice.

## H.1 Core Agricultural Concepts

- **Kharif season** — the monsoon cropping season (sown with onset, harvested later in the year).
- **Sowing window** — the time interval when sowing is viable; delays beyond it reduce yield.
- **Rainfed agriculture** — crops dependent on rainfall (no irrigation). Highest sensitivity to onset/break timing.
- **Irrigated agriculture** — irrigation available; onset/dry-spell risk affects *how much* supplementary water is needed.
- **Crop water requirements** — how much water a crop needs at each growth stage.
- **Soil moisture** — stored water available to plants.
- **Germination requirements** — water needed for seeds to germinate.
- **Dry-spell sensitivity** — how damaging a dry period is at a given growth stage.
- **Crop stress** — loss of productive capacity under water deficit.
- **Contingency planning** — alternate crops / practices if the primary plan fails.

## H.2 The Crop Risk Chain

```
Monsoon forecast
       ▼
Rainfall risk
       ▼
Crop risk
       ▼
Sowing decision
```

## H.3 Recommendation Logic Must Be Rule-Based

```
Forecast
    + Crop information
    + Sow window
    + Soil type
    + Irrigation availability
    + Local agricultural practice
            ▼
    Recommendation
```

The decision layer should be **rule-based / agronomically justified**, not "our AI says sow tomorrow."

## H.4 Scenario Table (Map Forecasts → Decisions)

| Forecast | Crop situation | Recommendation |
| -------- | -------------- | -------------- |
| High onset probability + persistent rain | Rainfed crop | Proceed with sowing |
| Moderate onset + high dry-spell risk | Rainfed crop | Delay sowing |
| Low rainfall + irrigation available | Irrigated crop | Consider supplementary irrigation |
| High uncertainty | Any | Wait for confirmation |

## H.5 Regulatory / Authority Question

Who is authorized to issue an agricultural recommendation? The system is **decision support**; the final agricultural recommendation should be framed as advisory and traceable to agronomic logic / KVK-style guidance — not an autonomous directive.

## H.6 Kharif Crop Examples to Consider (Local Calibration)

Crops, sowing windows, water requirements, and dry-spell sensitivity vary by region. Recipes must be **region/block specific**, using local agricultural context — not generic.

## H.7 Agricultural Scenarios = Future Demo Cases

- **Scenario A:** Rainfall begins, persistence weak → False-onset risk.
- **Scenario B:** Monsoon established but 10–14 day rainfall reduction likely → Dry-spell/break risk.
- **Scenario C:** Break probability falls, rainfall probability rises → Possible revival.

## H.8 What the Farmer Actually Receives

They need: **"What should I do?"** — translated into local language, plain terms, with confidence. Not MJO phase numbers.