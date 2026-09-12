# SIH2026 — SIH26086 MONSOON DECISION SUPPORT

**Hyperlocal Monsoon Onset & Break Prediction System** (Ministry of Earth Sciences).
Transform subseasonal monsoon/rainfall signals into **block/cell-level agricultural
decision support**, with calibrated probability and provenance — a decision-support
prototype, **not** a deterministic weather-prediction system.

> Pilot grid: 0.25° cells in TN/MH/KA (304 cells). Grid cell ≠ official village/block
> boundary. Current mode is **historical/demo** (no live feed).

## Architecture

```text
Historical data (IMD/CHIRPS/ONI/NASA-POWER)
  -> frozen Phase H features (Group B, 64 features)
  -> frozen models (FREEZE_H): persistence for onset/break/dry_spell, XGBoost for revival
  -> ModelService (no training at serving time, no hardcoded probabilities)
  -> FastAPI + PostgreSQL (cells, forecasts, advisories, model_metadata)
  -> deterministic rule engine (probability -> band -> interpretation -> action)
  -> Groq explanation layer (rephrases deterministic facts ONLY; graceful fallback)
  -> React dashboard (cards / signal / recommendation / why / calibration / provenance)
```

## Quickstart

```bash
# 1. environment
copy .env.example .env        # fill in DATABASE_URL (+ optional GROQ_API_KEY)

# 2. backend API (port 8000)
python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000
# frontend API at http://127.0.0.1:8000 (static build) or Swagger at /docs

# 3. frontend dev (port 5173, proxies /api and /health)
cd frontend && npm install && npm run dev

# 4. database (optional seed/migrations already applied)
python -m src.database.seed    # idempotent: 304 cells + 4 model_metadata rows

# 5. demo self-check (reproduces the frozen regression)
python -m src.serving.demo
```

## Verified demo scenario

Cell `10.75_77.5`, date `2024-08-12`: false onset → dry spell → revival signal →
**revival probability 0.6047** (reproduced live through the frozen-model serving path,
never hardcoded). Run `python -m src.serving.demo` to reproduce.

## Tests

```bash
python -m pytest tests/ -q     # backend: 142 passed (includes full-MVP integration)
cd frontend && npx vitest run  # frontend: 19 passed
```

## Documentation

- `reports/FINAL_PROTOTYPE_EVALUATION.md` — audit map + judge-ready self-evaluation
- `reports/PHASE_I_INTEGRATION_REPORT.md` — end-to-end integration + failure scenarios
- `reports/MVP_API_CONTRACT.md` — implemented API surface (Swagger at `/docs`)
- `reports/` — data, labeling, modeling, calibration, leakage & decision-rule reports
- `docs/README.md` — monsoon science/knowledge base (A–K)

Security: `.env` is git-ignored; credentials never leave the server; Groq key is
server-side only; CORS restricted to local dev/preview origins.