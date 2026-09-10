# Post-MVP Roadmap (Deferred Extension Points)

Everything below is intentionally deferred beyond Phase I. Deferring is a feature:
the frozen, leak-free core stays untouched while these extensions hang off it.

## Low-risk, high-value (paper-design next)

1. **District/village aggregate layer (GIS overlay).** Map 0.25° grid cells onto
   official village/block polygons *read-only* for *reporting only*, keeping the
   per-cell numbers and the "grid cell, not village" contract in every payload.
2. **Exportable bulletins.** Deterministic rendering of the existing advisory bundle
   to a one-page PDF (layout only — numbers still from the same envelope).
3. **Scheduled batch runner.** The API already returns everything; a cron job over
   all 304 cells × latest date would produce a "morning bulletin" with zero new ML.
4. **Persistence/climatology audit artifact.** `data/serving/persistence_params.json`
   already ships the G1 determinism snapshot; wire a CI check that fails on drift.

## Requires new (expensive) data before any claim change

5. **Live/operational IMD feed.** Same-day-grid ingest would turn historical/demo mode
   into a real service. It must reuse the frozen pipeline as-is, validate
   schema/range at the boundary, and keep the disappearance of data → 404/409 path.
6. **Post-2024 extension of the frozen matrix.** Running the Phase H pipeline on newer
   JJAS years then re-freezing would be a *modeling* phase (with the same leak
   discipline), not a serving change.
7. **Calibration on more recent anni.** ECE/Brier are currently 2022–2023; re-scoring
   the frozen revival on post-freeze years would report drift (not retrain).

## Product layer (no ML, no numbers)

8. **Bounded LLM rephrasing layer** — input = the deterministic bundle only; output
   must round-trip to the same numbers; every paraphrase flagged "rephrased".
9. **Auth / roles for extension officers & admins** (data is government-touch), plus
   audit log of who viewed which cell.
10. **Push notifications** for high-band transitions (revival ≥ 0.8) per subscribed cell.

## Explicitly out of scope (never planned)

Blockchain, IoT sensor integration, deep learning / new architectures, retraining at
serving time, chat agents that answer agronomy, and any change to the frozen models
while 2024 is still reserved as test.