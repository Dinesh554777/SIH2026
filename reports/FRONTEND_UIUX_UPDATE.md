# UI/UX Enhancement Update — Demonstrated Dashboard (Sections 1–5 of the UI Prompt)

Date: 2026-09-13
Scope decided with the user: proceed with UI-prompt sections 1–5 now (professional AgriTech vision, dashboard hierarchy, premium header/nav, location drill-down, map), using the master-build-prompt Phase 4/6/7 guidance for the map + advisory UI. Section 6+ (boundary maps, charts, timeline, alerts) remains parked until the rest of the prompt is pasted.

Everything below is proven by the frozen pipeline on the LIVE stack (backend `http://127.0.0.1:8000`, frontend `http://localhost:5173`).

## What was added

### Backend (additive, no frozen-artifact change)
- `src/serving/demo_hierarchy.py` — a clearly-labelled **DEMO/SIMULATED** administrative hierarchy
  (State → District → Block → Village) mapped to REAL pilot grid cells:
  Tamil Nadu → Thanjavur → Orathanadu → 3 demo villages → cells `10.75_77.5`, `10.75_77.25`, `10.0_76.25`.
  It is validated against the 304-cell registry at request time; `mode: "demo/simulated"` + a
  NOT-authoritative-GIS note are returned in every payload so honest framing is impossible to miss.
- New endpoints:
  - `GET /api/v1/geography/demo` — full demo tree (validated against registry).
  - `GET /api/v1/geography/demo/{village_id}` — resolve one village to its cell + path (404 for unknowns).
  - (Earlier in this build) `GET …/decision`, `…/village-advisory`, `…/deliver`, `…/demo/scenarios`.
- New offline tests: `tests/test_geography_demo_api.py` (7 tests) — asserts demo naming honesty,
  registry-valid cells, bilingual advisory, MOCK delivery, and that scenarios are computed not fabricated.

### Frontend (React 18 SPA, no new dependencies)
- **Premium sticky header** (`Header.jsx`): logo mark, product name, nav (Dashboard/Map/Forecast/Advisory/Analytics/Alerts with smooth scroll), language selector, model + mode chips. The `<h1>` and subtitle the existing tests depend on are preserved.
- **Location drill-down** (`LocationSelector.jsx`): State → District → Block → Village browse list, breadcrumb, search/autocomplete, "recent locations" persistence, plus the original 304-cell flat select + date picker as an "Advanced" fine-control fallback. All original testids (`cell-select`, `cell-meta`, `date-field`) and behavior are intact.
- **Monsoon status hero** (`MonsoonStatus.jsx`): the decision-driven status band (e.g. "Dry-spell risk") with false-onset + confidence + rules-version chips and the dominant decision chip.
- **Officer decision card** (`DecisionPanel.jsx`): SOW/WAIT/MONITOR/PREPARE/IRRIGATION_PREPARE action badge, evidence checklist (✓/✕), risk bars (onset/dry-spell/break from `risk_summary`), disclaimer. No probabilities are ever fabricated — nothing renders before real backend output.
- **Bilingual village advisory + delivery** (`VillageAdvisoryPanel.jsx`): EN ⇄ தமிழ் toggle, printable A4 `print_head`, plain offline text, and one-tap delivery over all seven channels (field worker / panchayat / notice print / SMS / IVR / WhatsApp / FPO). Delivery responses show the MOCK notice + full traceability (risk-assessment and delivery DB ids), and the IVR script where applicable.
- **Demo scenario strip** (`ScenarioSwitcher.jsx`): replays the five frozen dates; changing a scenario re-runs the recompute path (decision is computed deterministically, never hard-coded).
- **Interactive grid map** (`CellMap.jsx`): dependency-free SVG of all 304 pilot cells, region-labeled, click-to-select; honest note that boundaries await authoritative GIS (§6).

## Verification
- Frontend: `vitest run` → **23/23 passed** (15 original tests untouched + 8 new: hierarchy browse, decision card, bilingual advisory, MOCK delivery traceability, scenario replay, and old error/loading/provenance paths). Production `vite build` clean.
- Backend: full pytest regression → **281 passed, 0 failed** (baseline 274 + 7 new).
- Live end-to-end (via the Vite proxy): 3 real cells each produced forecast → decision → bilingual advisory → persisted delivery (trace ids found in Postgres), demo scenarios return the expected decisions (06-07 WAIT/false-onset, 08-12 IRRIGATION_PREPARE, …), geography endpoint returns the demo tree. FREEZE_H digest unchanged (`4f122044f8710b53`).

## Discipline notes
- Every new payload carries its honest labels: `mode: demo/simulated` for geography, `historical/demo` for data, `[MOCK …]` for delivery transport, and the existing "not live forecasts" banner remains on the dashboard.
- No boundary polygons, no fabricated village-level models, no hard-coded probabilities, no changes to frozen artifacts, no new dependencies.

## Next
- Paste the remainder of the UI/UX prompt (section 6 onward) for the full boundary map, charts/timeline, and alerts; fold it in with the same discipline. A full boundary map is intentionally parked on authoritative GIS.