# K. Evaluator Perspective

> How a scientifically sophisticated judge sees this problem — and the winning strategy.

## K.1 The Overall Verdict

| Dimension | Rating |
| --------- | ------ |
| Potential | HIGH |
| Execution risk | VERY HIGH |
| Scientific risk | VERY HIGH |
| Demo potential | HIGH |
| Innovation potential | HIGH |

**Verdict: Workable — only if scientific credibility is treated as the core feature.**

Do NOT try to win by claiming superior weather prediction. Win with:

> **Probabilistic monsoon-phase intelligence → local uncertainty → actionable sowing decisions → verified historical evidence.**

The **false-onset + dry-spell** use case is the centerpiece of the story.

## K.2 What Judges Like

- ✅ Clear agricultural impact
- ✅ Probabilistic rather than overconfident predictions
- ✅ Real historical validation (hindcasts over multiple seasons)
- ✅ False-onset demonstration
- ✅ Explainable recommendations
- ✅ Block/panchayat visualization
- ✅ Strong baseline comparisons (climatology + persistence)

## K.3 What Judges Will Question

- ⚠️ "Why can you predict 30 days ahead?"
- ⚠️ "What is your ground truth?"
- ⚠️ "Why should we trust your downscaling?"
- ⚠️ "Does your model actually beat climatology?"
- ⚠️ "How many seasons did you validate on?"
- ⚠️ "What happens when the prediction is wrong?"
- ⚠️ "Where does your village-level data come from?"

## K.4 The Common Rejection Pattern

**Dangerous submission:**
> "We used a Transformer + satellite data + LSTM and achieved 95% accuracy."

without demonstrating: baselines, uncertainty, out-of-sample testing, scientific definitions, real historical cases.

That is exactly what a domain expert can dismantle in Q&A.

## K.5 The Stronger Answer to "Why Believe You?"

> "We do not claim deterministic village-level weather prediction. We estimate probabilistic risk using large-scale climate signals and local historical behavior, then benchmark our predictions against climatology and persistence. The advisory layer explicitly communicates uncertainty."

## K.6 The Hidden-Assumptions Checklist (Answer Before Coding)

1. What exactly defines **monsoon onset**?
2. What rainfall threshold defines a **break**?
3. How long must rainfall persist to call it onset?
4. What constitutes a **false onset**?
5. What spatial unit will you actually demonstrate?
6. Do you have sufficient historical observations at that scale?
7. What is your ground-truth dataset?
8. What is your baseline?
9. How will you measure probabilistic forecast quality?
10. What happens when your prediction confidence is low?
11. Who is authorized to issue an agricultural recommendation?
12. How will crop-specific advice vary by region?

These questions matter more than LSTM vs Transformer vs XGBoost.

## K.7 The 25 Questions the Team Must Answer From Memory

### Scientific
1. What exactly is monsoon onset?
2. What is a monsoon break?
3. What is a false onset?
4. What is a dry spell?
5. What is monsoon revival?
6. Why is 30-day prediction difficult?
7. What is subseasonal prediction?
8. What are ENSO, IOD and MJO?

### Data
9. What is your ground truth?
10. What is your spatial resolution?
11. What is your temporal resolution?
12. How many historical years do you have?
13. How will you handle missing observations?
14. How will you prevent data leakage?

### ML/statistics
15. What is your baseline?
16. Why probability instead of deterministic prediction?
17. How do you evaluate probability?
18. What is calibration?
19. What is hindcasting?
20. Does your model actually outperform climatology?

### Product
21. What does the farmer actually receive?
22. What happens when confidence is low?
23. How does the system identify false onset?
24. How does a forecast become an agricultural recommendation?
25. Why is your system better than a normal weather forecast?

## K.8 The Complete Chain (Architectural Principle)

```
GLOBAL CLIMATE → ENSO/IOD/MJO → REGIONAL ATMOSPHERE → LOCAL CONDITIONS
→ HISTORICAL CLIMATOLOGY → RECENT RAINFALL
→ PREDICTION SYSTEM → ONSET/BREAK/REVIVAL
→ UNCERTAINTY → LOCAL RISK → AGRICULTURAL DECISION → FARMER/OFFICER
```

**Critical architectural principle:**
- ML/statistical models → prediction.
- LLM (if at all) → multilingual explanation / advisory wording / conversational querying.
- Decision engine → rule-based, agronomically justified.

**Don't make the LLM the forecasting model.**

## K.9 Feasibility at Hackathon Scale (Reality Check)

| Component | Difficulty | Hackathon feasibility |
| --------- | ---------- | --------------------- |
| Historical rainfall pipeline | Low | High |
| Climate-index ingestion | Low–Medium | High |
| Rainfall anomaly prediction | Medium | High |
| Block-level downscaling | High | Medium |
| 7–30 day probabilistic prediction | Very High | Risky |
| Onset/break classification | High | Medium |
| Crop advisory engine | Medium | Very High |
| Multilingual dashboard | Medium | High |
| Model verification | High | Essential |

## K.10 Team Fit (4–6 People)

| Role | Responsibility |
| ---- | -------------- |
| ML/Climate Lead | Forecasting + feature engineering |
| Data Engineer | Rainfall/climate datasets + preprocessing |
| Backend Engineer | APIs + prediction pipeline |
| Frontend/GIS | Block/Panchayat visualization |
| Agriculture/Research Lead | Onset definitions + advisory logic |
| Pitch/QA | Validation + demo + judge questions |

With 3–4 people: collapse advisory and research roles. Don't build six modules.

## K.11 Core Research Question to Answer Now

> **"What decision-support gap remains after existing IMD/MoES hyperlocal weather forecasting capabilities?"**

Answer order for the project:

1. What already exists? (IMD/MoES systems, onset methodology, NWP, advisories)
2. What data actually exists to solve the gap? (inventory datasets)
3. What scientifically defensible prediction approach can use that data?
4. What technology/model should be used? (LAST, never first)