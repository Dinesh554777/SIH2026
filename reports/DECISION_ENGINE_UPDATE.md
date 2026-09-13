# Decision Engine & Bilingual Advisory Build (Protocol v2)

**Scope:** Master build prompt (33 sections) — backend core implemented in its
phases 1-3, 5-7 (DB + decision engine + advisory + delivery + demo scenarios).
Phase 4 (officer dashboard UI) and Phase 8 (deployment docs) are the next gates.
Frozen Phase H science is untouched (digests unchanged); API extensions are additive.

## Reuse, not rewrite (audit → build)
Everything below runs on the existing frozen pipeline:
`ModelService.predict` → `build_cards_with_bands` → new **decision engine** →
bilingual advisory → delivery traceability. No probability is ever fabricated.

## What was built

### 1. Configurable decision thresholds (`data/decision/`)
- `decision_rules.json` — onset/dry-spell/break thresholds + false-onset rule knobs +
  ordered decision priority. Loaded by the engine (env override `SIH_DECISION_RULES`);
  **never hard-coded in the UI**. This satisfies §5/§23.
- `crop_profiles.json` — paddy/groundnut/cotton (sowing window, `sow_confidence_needed`,
  dry-spell sensitivity, irrigation availability) — §"Agricultural context".

### 2. Decision engine (`src/decision/`)
- `signals.py` — deterministic derived signals: **false-onset risk** (low/medium/high)
  from validated rainfall+persistence+drying signals (evidence-driven, explicitly not a
  trained probability) and coarse **monsoon status** (pre-onset / unstable / stable /
  dry-spell risk / break risk / recovery).
- `engine.py` — composite **SOW / WAIT / MONITOR / PREPARE / IRRIGATION_PREPARE**,
  ordered by configured priority; `critical_reasons` ("Why") + evidence checklist
  ("Why WAIT?" per §8); confidence (high/medium); versioned thresholds; no
  Groq/LLM dependency. `decision_from_serving()` adapts the existing serving bundle.
- `advisory.py` — **EN + Tamil** village advisory in the required print format
  (§13): VILLAGE / DATE / MONSOON STATUS / ACTION / WHY? / NEXT REVIEW / CONTACT.
  Tamil copy is simple farmer language, no probability jargon (§12, §20).
- `delivery.py` — last-mile channel generators (§14-15): field_worker, panchayat,
  notice_print (A4), sms, **ivr** (▶ PLAY ADVISORY script), whatsapp, fpo. Transport
  is MOCK; nothing fakes delivery success.

### 3. Database traceability (migration `0004`, §18-19)
New ORM models + Alembic migration:
`risk_assessments` (decision, confidence, all risks, evidence, thresholds_version),
`advisory_deliveries` (channel, language, status, issued_by, payload, mock_notice,
delivered_at), `agricultural_context`, `monsoon_events`. Decision-layer FKs reference
`forecasts`/`cells`; scientific tables untouched. `src/database/decision_repository.py`
is idempotent and validates before write.

### 4. API (additive)
- `GET /api/v1/cells/{id}/decision?date&crop&season`
- `GET /api/v1/cells/{id}/village-advisory` (EN+TA, printable)
- `GET /api/v1/cells/{id}/deliver?channel=...` (generates + persists traceability)
- `GET /api/v1/demo/scenarios` (5 pivot dates on the REAL frozen models)

### 5. Demo scenarios (§21-22, §30)
Computed live from the frozen pipeline, never hardcoded. Judged output:
2024-06-07 **WAIT** (false-onset risk HIGH), 2024-08-08 **MONITOR**,
2024-08-11 **MONITOR**, 2024-08-12 **IRRIGATION_PREPARE**, 2024-09-29
**IRRIGATION_PREPARE**.

## Verification
- New tests: `tests/test_decision_engine.py` (17 offline) +
  `tests/test_decision_db.py` (7 live PG; empty-init reproducibility at head 0004).
- Full regression: **274 passed / 0 failed** (2 pre-existing warnings).
- Production DB migrated 0003 → 0004; live API restarted (127.0.0.1:8000);
  all endpoints smoke-tested with persistence (risk_assessment and delivery rows).

## Known limits / next gates
- Tamil copy is authored (not LLM-generated) and requires dialect review by an
  agronomist / extension partner before Level 2.
- `agricultural_context` and village-level data remain demo/simulated (no
  authoritative GIS boundaries — prior gate).
- **PHASE 4** (officer dashboard drill-down + map + advisory UI) and
  **PHASE 8** (.env/README/API docs/deployment) are not built yet.