# D. Climate Drivers

> Principle: climate signals are **context**, not direct rainfall predictors. Do NOT think `ENSO → village rainfall`. Think of each signal as one piece of evidence feeding a probability estimate.

## D.1 ENSO — El Niño–Southern Oscillation

- Coupled ocean–atmosphere variability in the tropical Pacific.
- Has documented relationships with Indian monsoon variability (historically a weak-monsoon association with El Niño, but **not** deterministic).
- One piece of information — NOT "ENSO = exact village rainfall."

## D.2 IOD — Indian Ocean Dipole

- A pattern of sea-surface-temperature differences across parts of the Indian Ocean.
- Influences large-scale atmospheric circulation and can modulate monsoon rainfall.
- Again, an influence channel, not a direct local predictor.

## D.3 MJO — Madden–Julian Oscillation

- A large-scale tropical atmospheric disturbance that moves eastward.
- Modulates convection, rainfall, and circulation.
- **Especially relevant at subseasonal timescales** (weeks) — this matches SIH26086's 7–30 day horizon better than ENSO/IOD.

**Priority note:** for a subseasonal (intraseasonal) problem, MISO/MJO-style phase information is the more natural driver. ENSO/IOD are seasonal-scale context.

## D.4 Other Signals

- Sea-surface temperature (regional + global patterns)
- Atmospheric pressure (monsoon trough, pressure gradients)
- Wind patterns (low-level jet / Somali jet strength)
- Humidity / moisture availability
- Convection indices
- Ocean–atmosphere interactions generally

## D.5 The Correct Conceptual Model

```
Historical rainfall
    + Recent rainfall
    + Atmospheric conditions
    + ENSO
    + IOD
    + MJO
    + Regional information
              ▼
      Probability distribution
```

## D.6 What to Record for Each Signal

- What information it actually provides
- At what timescale (seasonal vs subseasonal)
- Data source / index definition (e.g., Niño 3.4, DMI for IOD, RMM phases for MJO)
- How it enters the model (as a feature/condition, not as a direct predictor of local totals)
- Its limitations

## D.7 The "Signals Disagree" Case

Climate signals can conflict. When they do, the system must be able to express **low confidence / abstention** (see I.3) rather than force an answer.