# SIH26086 — MVP API Contract

Date: 2026-07-07 · Updated 2026-09-12 · Status: **IMPLEMENTED — verified by the
Phase I-F integration suite and live round-trip.**

Conventions: REST over JSON, `application/json`, all timestamps ISO-8601 UTC (with a
`local_date` convenience for the JJAS seasonal calendar). Responses always include a
`provenance` block so judges can verify the frozen contract. No auth for the MVP.

Base path: `/api/v1`

## 0. Implemented surface (verified 2026-09-12)

| Endpoint | Purpose | Verified |
| --- | --- | --- |
| `GET /health` | Component health: api/model/data/database/groq; honest degraded state | ✅ |
| `GET /locations` | Alias for the pilot-cell catalog (304 cells) | ✅ |
| `GET /locations/{cell_id}` | Single cell + observation period | ✅ |
| `GET /api/v1/cells` | Pilot-cell catalog (304 cells) | ✅ |
| `GET /api/v1/cells/{cell_id}/forecast?date=` | Frozen-model probabilities + cards + calibration + provenance + persistence | ✅ |
| `GET /api/v1/cells/{cell_id}/advisory?date=` | Deterministic decision-support bundle + current signal | ✅ |
| `GET /api/v1/cells/{cell_id}/explain?date=` | Revival sensitivity table (no causality claim) | ✅ |
| `GET /api/v1/cells/{cell_id}/explanation?date=&lang=` | Deterministic advisory rephrased by Groq (fallback if Groq down) | ✅ |
| `GET /api/v1/model-info` | Frozen model strategy/provenance per target | ✅ |

CORS: allowed origins are `http://localhost:5173/4173` and `http://127.0.0.1:5173/4173`
(Vite dev/preview); override with `CORS_ORIGINS` (comma-separated) in `.env`. No
credentials/cookies → `allow_credentials=false`. The `.env`/API key never leave the server.

Payloads in sections 1–4 are reference schemas; the runnable Swagger UI (OpenAPI) at
`/docs` is the authoritative contract.

---

## 1. Locations

`GET /api/v1/locations`

Returns the resolvable pilot cells (304).

```jsonc
{
  "locations": [
    {
      "cell_id": "10.0_76.25",
      "lat": 10.0,
      "lon": 76.25,
      "region": "TN",                 // bbox-derived, NOT authoritative admin
      "admin_note": "grid_cell_only", // never claims a village/block boundary
      "last_observation_date": "2024-09-30"
    }
  ],
  "spatial_unit": {
    "type": "regular_grid_0.25deg",
    "description": "Approx 25 km x 25 km grid cell. Not an official village/block boundary.",
    "n_cells": 304
  }
}
```

`GET /api/v1/locations/{cell_id}` — single cell record (same schema).

## 2. Options / forecast

`GET /api/v1/cells/{cell_id}/forecast?date=YYYY-MM-DD`

`date` is the observation date *t* (defaults to latest available). The forecast applies to
day *t* using observations ≤ *t* (incl. the same-day's rainfall and neighbour rainfall —
see operational assumption in the product spec).

```jsonc
{
  "cell_id": "10.0_76.25",
  "forecast_date": "2024-09-05",
  "generated_at": "2024-09-05T18:00:00Z",
  "observations_used": {
    "imd_rain_t": 8.2, "imd_sum7": 41.0, "imd_sum14": 62.0,
    "th_accel": 1.4,
    "last_observed_day": "2024-09-05",
    "data_completeness": 1.0
  },
  "targets": {
    "onset":     { "probability": 0.008, "model": "persistence",   "band": "low",     "calibration_ece": 6.6e-05 },
    "break":     { "probability": 0.064, "model": "persistence",   "band": "moderate", "calibration_ece": 0.0018 },
    "revival":   { "probability": 0.78,  "model": "xgboost_groupB", "band": "high",   "calibration_ece": 0.0083 },
    "dry_spell": { "probability": 0.12,  "model": "persistence",   "band": "low",     "calibration_ece": 0.0018 }
  },
  "confidence": {
    "note": "Probabilities are calibrated outputs of frozen models (FREEZE_H). Bands are communication aids, not statistical guarantees.",
    "band_definitions": [
      {"band": "low", "range": [0.0, 0.30]},
      {"band": "moderate", "range": [0.30, 0.60]},
      {"band": "high", "range": [0.60, 0.80]},
      {"band": "very_high", "range": [0.80, 1.0]}
    ],
    "calibration": [
      {"state": "onset", "ece": 6.6e-05, "brier": 0.00792, "period": "2022-2023"},
      {"state": "break", "ece": 0.0018,  "brier": 0.0557,  "period": "2022-2023"},
      {"state": "revival", "ece": 0.0083, "brier": 0.00806, "period": "2022-2023"},
      {"state": "dry_spell", "ece": 0.0018, "brier": 0.0334, "period": "2022-2023"}
    ]
  },
  "provenance": {
    "freeze": "data/processed/FREEZE_H.json",
    "freeze_note": "2024 TEST DATA WAS NOT USED FOR FEATURE SELECTION OR MODEL SELECTION.",
    "train_period": "2015-2021", "validation_period": "2022-2023", "test_period": "2024",
    "model_ids": {"revival": "xgboost_groupB_64feats", "others": "persistence_markov"},
    "imputation": "SimpleImputer(median) train-only, medians frozen in FREEZE_H"
  }
}
```

Notes:
- Payloads above are **schema illustrations**; real values differ per cell/date. The demo
  scenario (`MVP_DEMO_SCENARIO.md`) pins exact values for cell `10.75_77.5`, 2024-08-12
  (revival = 0.6047).
- `targets.<t>.probability` is the **raw calibrated model probability**, never rounded
  to false certainty.
- `band` is the communication category derived from it.
- Embedded `observations_used` gives the officer the evidence surface for the "Why?" step.

## 3. Advisory

`GET /api/v1/cells/{cell_id}/advisory?date=YYYY-MM-DD`

Derived from the forecast via the decision-support engine (rules document).

```jsonc
{
  "cell_id": "10.0_76.25",
  "forecast_date": "2024-09-05",
  "summary": "Recent rainfall acceleration and short-window rainfall patterns contributed to the higher revival probability.",
  "items": [
    {
      "state": "revival", "probability": 0.78, "band": "high",
      "agricultural_interpretation": "Wet conditions becoming more likely after a dry interruption.",
      "suggested_action": "Resume/prepare appropriate field operations; consider readiness for transplanting/irrigation scheduling.",
      "expert_validation": "Agronomic rule — requires expert validation; recommendation only."
    },
    {
      "state": "dry_spell", "probability": 0.12, "band": "low",
      "agricultural_interpretation": "Near-term rainfall interruption risk is low.",
      "suggested_action": "No immediate water-conservation pull-back advised.",
      "expert_validation": "Agronomic rule — requires expert validation; recommendation only."
    }
  ],
  "disclaimer": "Decision-support suggestion, not an agronomic guarantee. Does not predict deterministic rainfall."
}
```

## 4. Explainability

`GET /api/v1/cells/{cell_id}/explain?date=YYYY-MM-DD` (optional, can be fused into advisory)

```jsonc
{
  "contributors": [
    {"feature": "th_accel", "value": 1.4, "role": "recent rainfall acceleration (2nd highest gain feature, revival model)"},
    {"feature": "imd_sum7", "value": 41.0, "role": "7-day rainfall accumulation"},
    {"feature": "th_wet_streak", "value": 1, "role": "consecutive wet days"}
  ],
  "model": "xgboost_groupB_64feats",
  "caveat": "Feature importance is descriptive, not causal."
}
```

## 5. Error handling (MVP)

| Code | Meaning |
| ---- | ------- |
| 404 | unknown cell_id or date outside JJAS / before data start |
| 422 | malformed date or params |
| 409 | insufficient observations for that day (data_completeness < threshold) — returns the intake-level message, not a fake number |
| 500 | model artifact load failure (startup) |

## 6. Explicitly out of scope (no endpoints yet)

- Batch "all cells" endpooint (deferred; used for demo precompute internally if needed)
- Authentication, user profiles, rate limits
- Historical re-forecast API (used only offline in the demo script)