# SIH26086 — MVP Decision-Support Rules

Date: 2026-09-07 · Status: **DRAFT — all agronomic rules require expert/extension validation.**

Design contract: models produce **probabilities**; decision rules convert them to
**interpretation + suggested action**; the LLM (if used) only rephrases the output of the
rules — it never forecasts, never sets thresholds, and never produces a probability.

---

## 1. Probability → band mapping (communication)

| Band | Range | Language example |
| ---- | ----- | ---------------- |
| low | [0.00, 0.30) | "Unlikely — but monsoon states can shift within days" |
| moderate | [0.30, 0.60) | "Possible — watch weather bulletins" |
| high | [0.60, 0.80) | "Relatively likely" |
| very high | [0.80, 1.00] | "Very likely" |

Bands are communication aids. The raw calibrated probability is always displayed.

---

## 2. Target semantics (from `src/labels/definitions.py` + freeze doc)

- **Onset day** — first sustained onset (3-day sum ≥ 20 mm with a trace sustain look-ahead).
  Begins the season. Rare single-day event (train p01 ≈ 0.0082).
- **Break day** — ≥ 5 consecutive dry days (< 2.5 mm) after onset.
- **Revival day** — the first wet day (≥ 2.5 mm) ending a break.
- **Dry-spell day** — ≥ 7 consecutive days < 1.0 mm (agricultural soil-moisture stress);
  sticky state.

---

## 3. Rule table (deterministic, Markov/persistence-first + revival ML card)

Every card reads: state, probability (raw), band, interpretation, suggested action,
expert-validation flag. Rules below rely on **current-day state** of the targets
(because the frozen models forecast the active state on day *t*).

### 3.1 Onset

| Probability | Band | Interpretation | Suggested action | Expert-validated? |
| --- | --- | --- | --- | --- |
| < 0.30 | low | "Seasonal rains not yet established here" | Continue pre-sowing preparation; do not plant on false onset | YES (operational standard) |
| 0.30–0.60 | moderate | "Onset may be near" | Monitor daily; align with lead' state across neighbour cells before committing | YES |
| ≥ 0.60 | high/very high | "Onset rains likely establishing" | Proceed with sowing/transplanting only after confirming actual sustained rain | YES |

### 3.2 Break

| Probability | Band | Interpretation | Suggested action | Expert-validated? |
| --- | --- | --- | --- | --- |
| < 0.30 | low | "Continuous monsoon flow expected" | No conservation pull-back needed | YES |
| 0.30–0.60 | moderate | "Break conditions possible" | Prepare irrigation plans; watch 5-day outlook | YES |
| ≥ 0.60 | high/very high | "Break conditions active/likely" | Trigger irrigation scheduling; conserve water; alert farmer groups | YES |

### 3.3 Revival (ML card)

| Probability | Band | Interpretation | Suggested action | Expert-validated? |
| --- | --- | --- | --- | --- |
| < 0.30 | low | "Rains not yet resuming" | Continue break posture; conserve | YES (definitions) |
| 0.30–0.60 | moderate | "Revival becoming more likely" | Advance transplanting/fertilizer preparation; stay flexible | FLAG: expect tolerance |
| ≥ 0.60 | high/very high | "Rainfall resumption likely today" | Resume operations; apply F&F based on actual rain | FLAG: expect tolerance |

The revival card is the one place ML beats persistence; it is the "why upgrade the demo"
moment (th_accel contributes).

### 3.4 Dry spell

| Probability | Band | Interpretation | Suggested action | Expert-validated? |
| --- | --- | --- | --- | --- |
| < 0.30 | low | "No soil-moisture stress yet" | Normal operations | YES |
| 0.30–0.60 | moderate | "Agricultural dry spell possible" | Pre-mobilize water; schedule irrigation windows | YES |
| ≥ 0.60 | high/very high | "Dry spell active/expected" | Withhold non-essential irrigation; prioritize high-value crops; adjust to critical growth stages | YES |

---

## 4. Aggregation rules (multi-cell)

- A plus-sign state across ≥ 60% of a district's cells → district-level advisory priority.
- Do NOT average probabilities across cells for a "district number"; report counts of cells
  in each band instead (dishonest averaging discouraged).
- No single-cell → district claim (cells are 0.25°, not districts).

---

## 5. LLM role (bounded)

Allowed:
- Rephrase the rule-table interpretation into plain, local-friendly language.
- Summarize the "why" from the frozen model's explanatory features (th_accel,
  imd_sum7, wet streaks) with a descriptive caveat.

Forbidden (fail-fast validation):
- Generating any new probability, adjusting a threshold, or producing a deterministic
  "rain will/won't occur" statement.
- Introducing claims about climate causation (feature importance is descriptive only).

## 6. Guardrails / honesty copy

- Every card carries "Probability is a calibrated model output, not a guarantee."
- The system never says "a break will NOT occur" — only states current probability.
- If data completeness < threshold → "Insufficient data" card instead of a number.
- All agronomic suggestions are flagged expert-validation-needed until an extension officer
  approves the mapping table.