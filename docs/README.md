# SIH26086 — Knowledge Base

**Hyperlocal Monsoon Onset & Break Prediction System (Block/Village Scale)**
Organization: **Ministry of Earth Sciences (MoES)** | Type: **Software** | SIH 2026

---

## Purpose

This is a research-first knowledge base for the SIH26086 problem statement. It exists **before any development**. The goal is to understand the science, the data, the validation, and the agricultural decision problem so that technology choices become obvious later.

> The one-sentence understanding:
> **SIH26086 asks you to estimate the probability of important monsoon phase transitions (onset / break / revival) at a very local scale (block/village) over subseasonal horizons (7–30 days), quantify how uncertain those estimates are, validate them against historical observations, and translate them into useful agricultural decisions.**

---

## Knowledge Map (A–K)

| Section | File |
| ------- | ---- |
| A. Official Problem Statement | `a-official-ps.md` |
| B. Existing MoES/IMD Systems | `b-existing-moes-imd-systems.md` |
| C. Monsoon Science | `c-monsoon-science.md` |
| D. Climate Drivers | `d-climate-drivers.md` |
| E. Forecast Science | `e-forecast-science.md` |
| F. Spatial Science (Downscaling) | `f-spatial-science.md` |
| G. Validation & Hindcasting | `g-validation.md` |
| H. Agriculture | `h-agriculture.md` |
| I. Decision Science | `i-decision-science.md` |
| J. Product | `j-product.md` |
| K. Evaluator Perspective | `k-evaluator-perspective.md` |

---

## The Core Intellectual Model

```
The farmer's question: "Should I sow now?"
                 │
                 ▼
       Is monsoon actually established?
                 │
                 ▼
          FALSE ONSET RISK?
                 │
                 ▼
   Will a break / dry spell follow?
                 │
                 ▼
        PROBABILISTIC FORECAST
                 │
                 ▼
            UNCERTAINTY
                 │
                 ▼
      LOCAL AGRICULTURAL DECISION
```

---

## Reasoning Chain (in this order, always)

**Science → Forecast → Uncertainty → Agriculture → Decision**

NOT: **Dataset → ML → Dashboard**

---

## The Master Research Question

> **"What decision-support gap remains after existing IMD/MoES hyperlocal weather forecasting capabilities?"**

This question must be answered **before choosing any ML algorithm**. The government already provides hyperlocal weather forecasts (see section B). Your project must fill the gap — not duplicate it.

---

## Decision Chain (informal)

```
Prediction → Probability → Economic/agricultural consequence → Decision
```

## The Two Baselines That Matter

1. **Climatology** — "what happens historically at this location/time-of-year?"
2. **Persistence** — "assume today's monsoon state continues"

Your model must demonstrably beat both. This is how you answer "why should we believe you?"

---

## Design Documents (Phase 3 — Pre-Implementation Specs)

Once the problem is understood, the following **design documents** define the system before any ML pipeline code:

| Document | Contents |
| -------- | -------- |
| `../PROJECT_REQUIREMENTS.md` | Prediction targets, scientific definitions (documented as assumptions), horizons, spatial resolution, principles, scope |
| `../SYSTEM_ARCHITECTURE.md` | Full pipeline: data → quality → features → state classifier → forecasting tiers → probabilistic output → downscaling → verification loop → decision engine → explainability → dashboards |
| `../DATA_DICTIONARY.md` | Input/output variables, labels, thresholds registry, provenance schema |
| `../MODELING_PLAN.md` | Baseline-first modeling, leakage rules, T2 guard, decision thresholds |
| `../EVALUATION_PLAN.md` | Hindcast protocol, metrics (Brier, calibration, skill vs baselines), anti-patterns |
| `../DATA_SOURCES.md` | Dataset inventory: provider/resolution/period/license/limitations |

---

## Current Stage

**Phase 3 — Design documents complete (research/design). ML pipeline implementation NOT started — blocked until documents are approved.**

Next research phase: **"What already exists?"** → **"What data exists?"** → **"What defensible approach?"** → then technology.