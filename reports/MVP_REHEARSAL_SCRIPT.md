# MVP Rehearsal Script (60 s, officer framing) + Judge Q&A Drill

Run-up (before the timer):
- Start server: `python -m uvicorn src.serving.api:app --host 127.0.0.1 --port 8000`
- Warm once: open http://127.0.0.1:8000 and click "Revival" (loads XGB, ~2 s).
- Reset to default state before the room walk-in.

## The 60-second walkthrough (officer script)

**Anchor:** "We are standing on a monsoon Monday in a *0.25° pilot grid cell* — about 25×25 km.
We're not naming villages or blocks; the government's grid is our unit of honesty."

| Time | What the presenter does | What the screen shows / what you say |
|---|---|---|
| 0–5 s | Load, click **Dry spell eve (2024-08-08)** | All four cards. Say: "Three of the four cards are persistence: yesterday was dry, so today stays likely dry. These are *calibrated* Markov probabilities, not moods." |
| 5–20 s | Point at band legend + calibration strip | "Probabilities fall into four bands. We print the validation calibration (ECE/Brier) because these are model outputs — written for a district ag officer, not a bettor." |
| 20–40 s | Click **Revival (2024-08-12)** | "Notice the *only ML card* — revival, from a frozen XGBoost on 64 rainfall-pattern features — jumps to 60% on trace rain while persistence lags. This is where machine learning earns its keep. And 'why' is inspectable: the acceleration of the 3-day rainfall is the lefthand driver — descriptive, not causal." |
| 40–50 s | Scroll to guidance + disclaimer | "The advisory is decision support: bands → interpretation → suggested action, mechanically checked, with disclaimer. Something an extension officer can stand behind." |
| 50–60 s | Show provenance JSON footer | "Every number carries freeze provenance: model FREEZE_H, train 2015–2021, validation 2022–2023, digest 4f122044f8710b53. The 2024 numbers you see before you were never used to tune anything. That is the whole slide." |

**Exit line:** "Small, frozen, leak-free, reproducible: one command recreates every number you saw."

## Pre-demo checklist (tick all before opening the room)

- [ ] `python -m pytest tests/ -q` → 68 passed (fresh)
- [ ] `python -m src.serving.demo` ends with `CHECK ... (PASS)` (revival 0.6047 on 2024-03)
- [ ] Server running; `/health` returns status ok + digest 4f122044f8710b53
- [ ] UI loaded once (pre-warm) — no red error card visible
- [ ] Screen at 100% zoom; demo buttons visible; no scroll surprises
- [ ] Backup plan ready: API-only answer path (curl the same endpoints) if UI breaks
- [ ] Battery/power + display adapter confirmed; presenter mic tested
- [ ] Copy of `MVP_KNOWN_LIMITATIONS.md` printed beside laptop (for tough questions)

## Judge Q&A drill (9+1 expected questions with 1–2 line answers)

1. **Is this really AI?** — Only where ML won honestly: easing-away revival is XGBoost
   (PR-AUC 0.949, val 2022-23); onset/break/dry-spell stay frozen persistence because
   no ML beat it. A defensible engineering choice, documented in FREEZE_H.json.
2. **Why not villages/blocks?** — We support 0.25° grid cells; claiming admin units
   would be dishonest on the current data. The UI says grid cell everywhere.
3. **Where’s your 2024 test result?** — In `test_2024_frozen.parquet` (used once,
   after freeze). The demo’s 0.6047 revival is that frozen-model output reproduced live.
4. **Isn’t persistence cheating?** — Persistence is the floor any ML must beat; on this
   problem it wins for three targets. We publish the comparison (Brier/PR-AUC) rather
   than hide it.
5. **Is this calibrated?** — ECE 0.008 (revival), 0.002 (break), 6.6e-05 (onset) on
   2022–2023; printed on screen and in provenance.
6. **Why is the advisory not a "do this" command?** — Agronomy is out of our data
   guarantee; we give calibrated state probability + band → suggested action with a
   disclaimer. Overclaiming would be the real product failure.
7. **Can an LLM drive this?** — No. Rule table is deterministic; any future LLM may
   only rephrase. No LLM touches a number here.
8. **What’s the failure mode?** — Missing/insufficient observations return 404/409 —
   never a fabricated number. Missing model artifact fails hard at boot.
9. **Scalability?** — 304 cells load in ~2 s (single matrix); per-request inference is
   microseconds. Grid-partitioning would be the production path.
10. **What did you NOT build?** — Auth, chat, GIS editing, blockchain, IoT, cloud
    infra, live feeds, deep learning, *and* retraining. All deliberate.