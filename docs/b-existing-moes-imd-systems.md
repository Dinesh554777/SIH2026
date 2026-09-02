# B. Existing MoES/IMD Systems

> Read this section first. Everything about SIH26086's positioning depends on **what already exists**.

## B.1 The Critical Fact

**MoES already has hyperlocal weather capability.**

- May 2026: MoES announced AI-enabled weather products providing localized information.
- Includes forecasts for **over 3,000 sub-districts**.
- Includes a **1-km-resolution rainfall forecast for Uttar Pradesh**.

**Consequence:** your project CANNOT claim "we will make weather forecasts hyperlocal." The government is already moving in that direction.

## B.2 The Corrected Research Question

Instead of "build hyperlocal weather," ask:

> **What is missing between existing hyperlocal weather forecasting and subseasonal monsoon-phase agricultural decision support?**

## B.3 The Ecosystem Map

```
             MoES / IMD
                 │
     ┌───────────┴───────────┐
     │                       │
Short/medium-range       Climate information
   weather                    │
     │                       │
     ▼                       ▼
 Local rainfall          Monsoon signals
                            │
     └───────────┬──────────┘
                 ▼
         SIH26086 (your system)
                 ▼
     MONSOON PHASE INTELLIGENCE
                 ▼
        ONSET / BREAK / REVIVAL
                 ▼
          AGRICULTURAL RISK
                 ▼
          FARMER DECISION
```

## B.4 The Broader MoES SIH 2026 Problem Set

SIH26086 sits inside a family of MoES problems (listed together under MoES):

| ID | Problem | Horizon |
| -- | ------- | ------- |
| SIH26081 | Hybrid AI/NWP Multi-Model Forecast Blending | forecast blending |
| SIH26082 | Air Pollution–Weather Coupled Forecasting | coupled modeling |
| SIH26083 | Extreme Heatwave Early Warning | medium-range |
| SIH26084 | Thunderstorm/Hail/Cloudburst Nowcasting | nowcasting (very short) |
| SIH26085 | Urban Flood Nowcasting | nowcasting + impact |
| **SIH26086** | **Hyperlocal Monsoon Onset & Break Prediction** | **subseasonal** |

**Insight:** the family covers the whole forecasting pipeline — blending (81), hazards (83–85), and SIH26086 = the **subseasonal monsoon-phase** component feeding agricultural decisions. Study where your problem sits within the pipeline.

## B.5 NWP — Numerical Weather Prediction

NWP = using mathematical/physical models to simulate atmospheric evolution:

```
Atmospheric observations → Initial state → Physics equations → Numerical model → Future state → Forecast
```

SIH26086 should be understood as:

```
Observations
  + NWP information
  + Climate signals
  + Historical climatology
  + Local characteristics
        ▼
Subseasonal probabilistic intelligence
```

NOT only: `Historical rainfall → ML`.

## B.6 IMD's Official Onset Methodology (Study Carefully)

- IMD defines an operational **onset date over Kerala**.
- **Normal onset date: 1 June**, standard deviation ≈ **7 days**.
- IMD has issued operational onset forecasts **since 2005** using an **indigenous statistical model**.

**Your research question:** how is official monsoon onset defined and forecast at the *large/regional scale*, and how does that differ from the *block/village-level onset* concept in SIH26086?

That distinction (regional onset vs. local onset) can become one of your strongest research points.

## B.7 Impact-Based Forecasting (MoES Direction)

MoES is moving toward **impact-based weather services** (integrating hazard information with exposure).

Progression:

```
Weather → Hazard → Impact → Decision
```

Traditional: "Rainfall = 20 mm"
Impact-based: "Rainfall conditions create high risk for rainfed sowing"
Decision-based: "Delay sowing until rainfall persistence is confirmed"

For SIH26086, **Decision Support** is the central product concept.

## B.8 Existing-Advisory Question (Answer Before Building)

Don't ask "can we build a weather app?"
Ask: **"What information already exists, and what decision-support gap remains?"**

## B.9 Capability vs Opportunity Table

| Existing capability | SIH26086 opportunity |
| ------------------- | -------------------- |
| Weather forecasting | Monsoon phase forecasting |
| Short/medium range | 1–4 week (subseasonal) horizon |
| Regional/local weather | Block/village decision scale |
| Rainfall prediction | Onset / break / revival |
| Weather variable | Agricultural decision |
| Forecast | Probability + confidence |
| Generic user | Farmer / extension officer |

## B.10 Institutional Sources to Study

- **IMD** — operational onset, NWP, district/sub-district forecasts
- **MoES** — AI-enabled products, impact-based services
- **IITM** — climate research, monsoon intraseasonal oscillations
- **ISRO** — satellite observations, remote sensing products
- **Agriculture departments** — advisories, crop contingency plans
- **FPOs, KVKs** (Krishi Vigyan Kendras) — farmer-facing advisory channels