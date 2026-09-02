# C. Monsoon Science

## C.1 The Indian Summer Monsoon

A large-scale seasonal atmospheric circulation system driven by land–ocean temperature contrasts. It involves interactions between land, ocean, atmosphere, pressure, winds, moisture, temperature, and large-scale climate oscillations.

Monsoon behavior = active phases, breaks, and revivals — not a single "is it raining or not" state.

## C.2 The Phase Cycle

```
PRE-ONSET → ONSET → ACTIVE → BREAK → REVIVAL → ACTIVE → ... → WITHDRAWAL
```

This is closer to **state prediction** than ordinary rainfall prediction.

## C.3 Onset — Definition

The transition into a **sustained** monsoon rainfall regime.

- The important word is **sustained**.
- Heavy rain for 3 days followed by 6 dry days must NOT automatically be called onset — it may be a **false onset**.
- IMD's operational regional reference: onset over Kerala, normal 1 June ± 7 days, forecast with a statistical model since 2005 (see B.6).

Working definition requirements (must be answered *before* coding):
- What rainfall threshold defines onset?
- How long must rainfall persist to call it onset?
- What is the difference between *regional onset* and *local (block/village) onset*?

## C.4 False Onset ⭐ (centerpiece use case)

```
Rainfall spike
      │
      │   ███
      │  █████
      │ ███████
      │
      │              █  (sparse)
      │
      └──────────────────
        farmers interpret as onset → sow → rain vanishes → dry spell → crop stress
```

A sophisticated system says:

> "Initial rainfall detected, but persistence is insufficient to confidently classify this as established monsoon onset."

Instead of "monsoon arrived," the system says: **"Onset confidence: 42%. Significant dry-spell risk within 14 days."**

**This is the strongest demo and story for the whole project.**

## C.5 Persistence

Rainfall persistence ≠ "did it rain."

```
Day 1: 20 mm | Day 2: 0 mm | Day 3: 2 mm | Day 4: 0 mm   → weak persistence
Day 1: 18 mm | Day 2: 15 mm| Day 3: 22 mm| Day 4: 17 mm  → strong persistence
```

Onset detection must consider whether rainfall established a **sustained pattern**, not just presence/absence.

## C.6 Break / Dry Spell

A period when monsoon rainfall activity becomes **significantly suppressed**.

- A dry spell is not necessarily one dry day — usually a period of rainfall below a meaningful threshold.
- The exact definition must be **scientifically and regionally justified** (based on a chosen reference methodology/dataset), not an arbitrary number.
- Judges may ask "what definition of dry spell did you use?" — you must have a sourced answer.

Working definition requirements:
- What rainfall threshold defines a break?
- What duration counts as a break/dry spell?

## C.7 Revival

The transition back from break to active rainfall.

```
ACTIVE PHASE → BREAK → REVIVAL → ACTIVE PHASE
```

The system monitors **transitions between monsoon states**, and revival probability is one of the key outputs.

## C.8 Rainfall Concepts to Standardize

- Daily rainfall
- Weekly rainfall / cumulative rainfall
- Rainfall intensity
- Rainfall anomaly (departure from climatology)
- Number of rainy days
- Consecutive dry days
- Consecutive wet days
- Historical climatology at location/time-of-year

## C.9 Monsoon Intraseasonal Oscillations (MISO)

The monsoon has its own intraseasonal (= within-season, weeks) variability with active/break cycles. These oscillations are the scale SIH26086 operates at — the same regime as the subseasonal forecast horizon.

## C.10 Key Questions to Answer From Notes

1. What exactly is monsoon onset?
2. What is a monsoon break?
3. What is a false onset?
4. What is a dry spell?
5. What is monsoon revival?
6. Why is 30-day prediction difficult?
7. What is subseasonal prediction?