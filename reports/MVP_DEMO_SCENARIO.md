# SIH26086 — MVP Demo Scenario (reproducible, grounded in held-out 2024 data)

Date: 2026-09-07 · Status: **DRAFT — the demo script is part of the 36-h build, this file fixes the scenario contract.**

Goal of the demo: show an officer (judge-facing) a **false-onset → long dry spell →
high-confidence revival** lifecycle at a real 0.25° cell, using **2024 data that the frozen
models never saw during feature/model selection**.

## Scenario anchor

- Demo cell: **`10.75_77.5`** — lat 10.75, lon 77.50, grid cell (≈25 km box) in the TN pilot
  region. Registry field `admin_note: "grid_cell_only"` — never described as a village/block.
- Held-out period: **2022–2023 validation, 2024 test**. The 2024 numbers below come from
  `data/processed/phase_h_matrix.parquet` (observed labels) and
  `data/processed/predictions/phase_h/test_2024_frozen.parquet` (frozen-model outputs).
- The `H_FROZEN` revival model (XGBoost, 64 features, Group B) reports probabilities
  generated in the single post-freeze 2024 pass.

## Timeline (real observations, 2024)

| Date | Observed event | imd_rain_t (mm) | Dry-spell active | Break active | Revival day |
| ---- | -------------- | --------------- | ---------------- | ------------ | ----------- |
| 2024-06-07 | Early rain event ("onset" fires; 3-day sum ≥ 20 mm) | 40.13 | 0 | 0 | 0 |
| 2024-06-09 → 2024-08-11 | **Long dry interruption** (~64 days of dry-spell stress) | 0.00 most days | 1 | 1 | 0 |
| 2024-08-11 | Trace rain | 0.23 | 1 | 1 | 0 |
| 2024-08-12 | **Revival day** (first ≥ 2.5 mm after break) | 2.97 | 0 | 0 | 1 |
| 2024-08-13 | Rain continues | 1.99 | 0 | 0 | 0 |
| (later) 2024-09-29 | Another late revival | 8.91 | — | — | 1 |

## Frozen model outputs on the pivot days (real numbers)

| Date | Card | Model | Probability | Band | Note |
| ---- | ---- | ----- | ----------- | ---- | ---- |
| 2024-06-07 | onset | persistence | ~0.008 (clim/p01 range) | low | IE onset is a rare single-day state; a **false-onset win NOT claimed** — system stays calibrated |
| 2024-08-08 | dry_spell | persistence(p11) | ~0.92 | very high | sticky state: correct (dry spell still active) |
| 2024-08-08 | break | persistence(p11) | ~0.91 | very high | sticky state: correct |
| 2024-08-11 | revival | XGBoost H_FROZEN | 0.0000 | low | correctly quiet before the trace day |
| **2024-08-12** | **revival** | **XGBoost H_FROZEN** | **0.6047** | **high** | **the money moment: ML flags resumption on the actual revival day** |
| 2024-08-12 | break | persistence(p11) | ~0.91 | very high | lags the transition (sticky persistence) |
| 2024-08-12 | dry_spell | persistence(p11) | ~0.92 | very high | lags the transition (same reason) |
| 2024-09-29 | revival | XGBoost H_FROZEN | 0.986 | very high | late-season trace signal → strong response |

Notes on honesty:
- Persistence cards on the transition day (Aug 12) are necessarily laggy (they predict "the
  state is still active"); the demo frames this as a **known limitation** and the exact
  reason an ML revival card adds value. Freeze report: revival only.
- Onset card on Jun 7 is at clim rate — the demo does NOT claim a "false onset warning" win
  the system didn't actually produce; instead it shows that even a 40 mm day maps to a
  calibrated ~1% onset-day probability because onset is a rare, structurally-defined state.
  The narrative value is: the officer sees 40 mm + LOW onset probability and the explanation
  surface (`imd_cum_jjas` still below seasonal norm, break-track features) — a calibrated
  anti-hype signal.

## Demo flow (officer-facing, ~8 minutes)

1. Officer searches "near 10.75, 77.5" → cell picked, grid identity shown, admin caveat in
   footer.
2. **False onset card**: they set date 2024-06-07, see 40.1 mm alongside a Low onset card —
   the "why" shows this is one wet day, not sustained onset (3-day window semantics).
3. **Dry-spell eve**: date 2024-08-08 → dry_spell very-high, break very-high; advisory:
   "withhold non-essential irrigation; prioritize critical-stage crops".
4. **Revival day**: date 2024-08-12 → revival 0.60 band high; advisory: "rainfall resumption
   likely; resume field operations" — with `th_accel` listed as a top contributor (descriptive).
5. Officer toggles "Why?" on the revival card: sees `th_accel`, `imd_sum7`, wet streak for
   that date; provenance block shows FREEZE_H + "2024 not used for selection".
6. Officer checks a second cell (e.g., a MH cell `14.5_74.5`) to see per-cell differences —
   emphasizing cells, not averaged districts.
7. Close with the uncertainty/honesty framing (bands, ECE values, "probability, not certainty").

## What the demo intentionally does NOT show

- No village/block overlay; no district probability average.
- No deterministic "it will rain on X" statement.
- No LLM-generated forecast (the LLM, if present, only rephrases the rule output).
- No model retraining at demo time.

## Reproducibility

Demo inputs are fully reproducible from `FREEZE_H.json` + the two parquet files above via
the API contract endpoints. The demo script computes the 8 pivot rows offline and serves
them through the same decision-support engine used in production (no special-casing).