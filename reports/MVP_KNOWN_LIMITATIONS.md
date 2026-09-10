# MVP Known Limitations (SIH26086)

Honest, explicit statement of what the MVP does NOT do — for evaluators, for the
demo script, and for any follow-up planning. The MVP is a decision-support layer
over frozen 0.25° pilot-grid inference; nothing that follows is claimed by the system.

## 1. Data & Coverage

- **Grid cells, not villages/blocks.** All language in the product uses "pilot cell /
  grid cell (0.25°)". Administrative (village/block) boundaries are NOT mapped, and
  NAD-claims of regional capability are explicitly non-authoritative bbox guesses.
- **2024 is held out (by design).** Revival probabilities are produced by a model
  frozen on 2015–2021 train, validated on 2022–2023, and (as of freeze time)
  never seen 2024. The demo uses real 2024 inputs but the results were not used
  to change anything at freeze time.
- **Training horizon:** 2015–2021 only. Extreme or climate-shift behaviours after
  2021 are captured only insofar as the frozen imputation/parameters tolerate them.
- **Seasonal window JJAS only** (Jun 1–Sep 30). Requests outside the monsoon window
  return an explicit error; the system cannot reason about pre/post-monsoon.
- **No post-2024 data:** the latest served observation is 2024-09-30. Ongoing years
  require re-running the (Phase H) pipeline that produced the matrix.

## 2. Model & Inference

- **Revival is XGBoost on 64 features** with intended high-class-imbalance handling
  via scale_pos_weight; probabilities are model outputs, not ground truth. The
  calibration metric (validation ECE 0.00835) reflects 2022–2023 only.
- **Persistence is strong on break/dry_spell** (p11 ≈ 0.91) and near-zero on onset
  (p11 = 0.0). On dry-spell/break days the "ML card" (revival) may therefore be the
  only differentiating signal; this is by design but means single-target dominance
  can look path-dependent: today's director flow is the *model*, uncertainty is
  carried per-target and in the band histogram, not as a consolidated overall value.
- **Sensitivity is descriptive, not causal.** The `explain` endpoint shows
  one-feature-at-a-time deltas of the frozen model vs train medians; a noisy or
  extreme feature can dominate the delta. It must never be read as a causal claim.
- **Imputation:** SimpleImputer(median) on train statistics handles structural NaN;
  it does not model missing-data patterns beyond that.

## 3. Demo & Validation Reality

- **Demo is grounded but imperfect.** `10.75_77.5` 2024 shows a textbook transition
  (false onset → dry spell → revival) reproduced by the frozen models; the numbers
  in the demo script are *asserted equal* to the frozen outputs, not cherry-picked
  for a UI. Perfect story-telling is not claimed on every cell/date pair.
- **Historical/demo mode only.** Nothing fabricates a "live" feed. If the product
  moves to production, a real IMD-grid ingest (same-day obs) is required.

## 4. Product / UX

- **No auth, no personalization, no offline mode, no notifications.** Single-page
  static UI intended for a booth demo; not a hardened multi-user product.
- **No cloud / no deployment config.** Runs locally via uvicorn; no Docker/CI in repo.
- **Advisory text is template language (rules v1).** It is deterministic and safe,
  but not agricultural fine-tuning; disclaimers are returned with every payload.
- **LLM integration is explicitly out of the numeric/decision path.** If a later
  phase adds a language layer it may only *rephrase* the deterministic output.

## 5. Known Rough Edges

- **Consolevariants:**
  - Windows console prints of non-ASCII characters (e.g., "—") can appear garbled;
    the demo script avoids them.
  - The training-time boot print of the persistence transition table is informative
    noise on first import, not a data issue.
- **Model-loading cost:** first request after process start pays one matrix + model
  load (~2 s); subsequent requests are fast (all singletons).
- **`region` is a heuristic** (bbox attribution). If admin boundaries matter, the
  spatial-unit policy must change, which would invalidate parts of this MVP's
  conservative wording (source of `region_of` guess - see
  `src/modeling/common.py`).
- **Matrix size:** 370,880×97 in a single parquet is fine for a demo but would need
  a columnar/partitioning strategy for a production cell-oriented API.

## 6. What the MVP Deliberately Does NOT Do

No authentication · no payments · no user profiles · no social features · no
chatbot · no GIS editing · no blockchain · no IoT · no cloud infrastructure ·
no deep learning · no retraining on the fly · no fabricated data feeds ·
no village/block claims · no guaranteed agronomic advice.