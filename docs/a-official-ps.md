# A. Official Problem Statement

## A.1 Identity

| Field | Value |
| ----- | ----- |
| Problem ID | **SIH26086** |
| Organization | **Ministry of Earth Sciences (MoES)** |
| Type | Software |
| Title | **Hyperlocal Monsoon Onset & Break Prediction System (Block/Village Scale)** |

> Note: this repo's copy of the *exact* descriptive text (expected outcome, constraints) must be captured verbatim from the official SIH 2026 problem statement source before development. This document records the working interpretation.

## A.2 What the Title Means — Word by Word

### Hyperlocal
Not "Tamil Nadu will receive rainfall." Something closer to: **Tiruppur district → particular block → particular agricultural area**. Fine spatial resolution is the requirement — the output must be decision-relevant at local scale (block, panchayat, village cluster).

### Monsoon
Not "rain." The Indian monsoon is a **large-scale seasonal atmospheric circulation system** involving land–ocean–atmosphere interactions: pressure, winds, moisture, temperature, convection, and large-scale climate oscillations. Predicting its behavior is far harder than predicting tomorrow's rain.

### Onset
The transition into a **sustained** monsoon rainfall regime. The key word is **sustained** — three heavy rain days followed by nothing does not prove monsoon arrival; it may be a **false onset**.

### Break
A period during the monsoon season when rainfall activity becomes **significantly suppressed** (a dry spell following an active phase).

### Block/Village Scale
The spatial unit the forecast must be communicated at. See section F (Spatial Science).

## A.3 What the Problem is Actually Asking

The intended outputs (working interpretation):

- Monsoon **onset probability** (not just a date)
- Probability of a **break / dry spell**
- Probability of **revival**
- Local / block-level rainfall outlook
- Crop-specific recommendations, e.g. **sow now / delay sowing / arrange supplementary irrigation / wait for rainfall confirmation**

## A.4 Why the Problem Exists

The core farmer pain: significant loss if sowing happens during a **false onset** followed by a prolonged dry spell. The problem targets **intra-seasonal variability** rather than only seasonal rainfall totals.

## A.5 Three Problems Hidden Inside One

1. **Climate prediction** — extract useful signals from large-scale atmospheric/climate conditions (ENSO, IOD, MJO, historical rainfall, regional weather).
2. **Spatial downscaling** — District → Block → Panchayat/Village cluster. A major scientific challenge.
3. **Decision translation** — "65% probability of a dry spell" is not directly useful. Forecast → Confidence → Agricultural interpretation → Action.

## A.6 Key Framing Rule

Do **not** promise "accurate village rainfall 30 days ahead."
Frame the system as a **probabilistic decision-support system**.
That framing difference matters during judging.

## A.7 Scope Boundary (Honest Positioning)

Don't claim the prototype is an operational meteorological forecasting system. Position as:

> **"We demonstrate an operationally extensible decision-support architecture using historical/live-accessible data."**

## A.8 Source of Truth Note

Third-party summaries (SIH Buddy, CodeHunters, SIH research explorer) are **analysis, not official requirements**. The underlying problem statement data comes from SIH; scoring/build plans are third-party frameworks. Always verify against the official statement.