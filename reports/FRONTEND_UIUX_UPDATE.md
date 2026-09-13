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

### Sections 6–11 folded into the new routed officer-dashboard shell (2026-09-13, second round)
- **New shell is canonical** (user decision): CommandBar + Sidebar + Dashboard routes wire all five tenant surfaces. `App.jsx` gained the `cellsRisk` state (best-effort `_cells-risk` fetch keyed to the active date) and a clean `<Routes>` block (fixed a prior unclosed-`Route` JSX syntax error). Breadcrumb now renders district/block safely for flat search-selected villages.
- **Risk analysis cards** (`RiskCards.jsx`): three honest cards (onset/dry-spell/break) with rounded real probabilities (e.g. 91%) + band labels + risk-band window text; the pause risk card carries an action by decision-engine authority only.
- **Forecast timeline** (`ForecastTimeline.jsx`): past observed reads, current model read, honest "future = scenario" note; scenarios re-run the real recompute path.
- **Monsoon status hero** (`MonsoonStatus.jsx`): decision-band hero (`status-hero`) + where/when/village line (`status-where`).
- **Interactive risk map** (`MapExplorer.jsx`, replaces flat grid): 304-cell Leaflet grid with per-cell risk coloring from the frozen `cells-risk` payload plus a whole-grid **risk legend** (`risk-legend`: "Risk level (whole grid)", level counts, note "derived from frozen model probabilities · 2024-08-12"), and a **village search** (role `searchbox`) resolving village → pilot cell decision. Search + select re-use one `cell-select` control so the original testids stay unique.
- **Action centre / location recommendation** (`DecisionPanel.jsx` heading + location recommendation region) and the intel-panel re-work of `MonsoonStatus`/`VillageAdvisoryPanel` (fn-* ids, channels, VoicePlayer) keep exact legacy testids (`advisory-lang`, `advisory-preview`, `delivery-result`) for the untouched §1–§5 tests.

## Verification
- Frontend: `vitest run` → **27/27 passed** (15 original tests untouched + 12 new including the §6–§11 panels, risk legend, timeline honesty, and village→cell resolution). Production `vite build` clean (built in ~7s).
- Backend: full pytest regression → **284 passed, 0 failed**.
- Live end-to-end (via the Vite proxy / direct): cells-risk (304 cells), forecast → decision → bilingual village-advisory → MOCK delivery all verified on `2024-08-12`. FREEZE_H.json + phase_h_matrix.parquet digests unchanged (`4f122044f8710b53…` / `a87c5d239f7a6b9a…`).

## Discipline notes
- Every new payload carries its honest labels: `mode: demo/simulated` for geography, `historical/demo` for data, `[MOCK …]` for delivery transport, and the existing "not live forecasts" banner remains on the dashboard.
- No boundary polygons, no fabricated village-level models, no hard-coded probabilities, no changes to frozen artifacts, no new dependencies.

## Next
- Paste the remainder of the UI/UX prompt (§12 onward) and fold it in with the same discipline. The frozen decision engine remains the sole action authority; band thresholds are unchanged. A full boundary map is intentionally parked on authoritative GIS.