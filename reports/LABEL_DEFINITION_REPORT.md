# LABEL DEFINITION REPORT — SIH26086 Monsoon Onset / Break / Revival / Dry-Spell

**Phase A · label engineering** · generated 2026-09-06
**Ground truth:** IMD 0.25° daily `RAINFALL` (`ind<year>_rfp25.nc`, validated, 0 % missing in
2015–2024). Grid = 304 IMD cells inside the union of the three state boxes in
`config/project.yaml` (TN 10.0–13.5N/76.2–80.4E, MH 17.5–19.5N/73.2–75.0E, KA
11.5–12.6N/76.0–77.2E). Cell selection filter in `src/load.py:select_pilot_cells`
(≥90 % valid IMD days and ≥1 % wet days) drops 185 empty "corner" cells of the
domain rectangle and any sea/desert-like cell.

> **CALIBRATION_PENDING flags.** `TRAINING_DATA_DESIGN.md` specifies the *structure*
> of all four labels but no numerical thresholds. The numbers below are the
> operational proxy adopted here and are implemented as single-source constants in
> `src/labels/definitions.py`. When official MoES/village checklists arrive, ONLY
> those constants change (never a silent threshold change — see engineering rules).

## 1. Definitions

| Label | Definition | Threshold | Code constant |
| --- | --- | --- | --- |
| **wet day** | IMD R ≥ 1 mm | 1.0 mm | `WET_DAY_MM` |
| **monsoon onset** | first JJAS day *t* with 3-day trailing sum S₃(t) = R(t−2)+R(t−1)+R(t) ≥ 20 mm **and** "sustained": R ≥ 2.5 mm on ≥ 1 of the next two days (t+1, t+2); declared **once per cell-year** | 20 mm/3d, sustain 2.5 mm | `ONSET_*` |
| **false onset candidate** | day where S₃ ≥ 20 mm but the sustain check fails (rains stall immediately) — recorded, never declared onset | — | `ONSET_*` (audit only) |
| **monsoon break** | run of ≥ 5 consecutive post-onset days with R < 2.5 mm; active on **every day of the run** | 5 d, 2.5 mm | `BREAK_MIN_DAYS`, `BREAK_MM` |
| **revival** | first post-onset day with R ≥ 2.5 mm after a matured (≥ 5 d) break run | 2.5 mm | `REVIVAL_MM` |
| **agricultural dry spell** | run of ≥ 7 consecutive post-onset days with R < 1.0 mm (cropping window) | 7 d, 1.0 mm | `DRY_SPELL_MIN_DAYS`, `DRY_SPELL_MM` |

*Rationale for proxy numbers.* 1.0 mm wet-day and 2.5 mm "operational drizzle" cutoffs match the
IMD-vs-CHIRPS comparison (`RAINFALL_DATASET_COMPARISON.md`) and IMD operational practice; the
20 mm/3-day cumulative + sustained-rain criterion follows the design doc's
"cumulative ≥ threshold sustained rain" wording with a 3-day smoothing; the ≥5-day
break and ≥7-day dry-spell lengths follow kharif-cropping stress literature.

## 2. Algorithm (per cell-year)

```
JJAS window = 2015-06-01..2015-09-30 etc. (122 d/yr)
S3(t) = rolling 3-day sum over t-2..t            (require 3 valid days, else skip)
onset   = min{ t : S3(t)≥20 AND exists k∈{t+1,t+2}, R(k)≥2.5 }
          else none (no_onset)
break   = after onset: maximal runs {t: R(t)<2.5} of length ≥5   → break_active=1 in-run
revival = min{ t > end(run) : R(t)≥2.5 } for each matured break run
dry     = after onset: maximal runs {t: R(t)<1.0} of length ≥7   → dry_spell_active=1 in-run
```

All run searches are **post-onset** (`start = onset_idx`): the second criterion is the
sowing-relevant "has the monsoon become established" signal, and dry spells are studied in
the cropping window.

**Missing data.** If > 10 % of JJAS days in a cell-year are invalid (IMD `-999`), the whole
cell-year is `insufficient_data` and all labels = NaN. Within-run missing days are counted as
dry (a missing observation must never *shorten* a dry/break run). No cell-year in the pilot
domain triggers this (IMD validated 0–0.8 % missing; max 0 missing 2015–2023, 0 for 2024 after
patch). `0 / 3040` cell-years flagged.

## 3. Validation & outcome statistics (304 cells × 10 years = 3,040 cell-years)

| Statistic | Value |
| --- | --- |
| Onset declared | 2,981 cell-years (98.1 %) |
| No onset (SW monsoon never established) | 59 cell-years (1.9 %) — all semi-arid interior TN/low-rain cells |
| Onset month distribution | Jun 1,974 · Jul 540 · Aug 325 · Sep 142 |
| Onset day-of-season (Jun 1 = 1), mean / median / p90 | 28.7 / 18 / 65 |
| Cell-years with onset after Aug 30 (near-window-late) | 151 (4.9 %) — interior TN rain-shadow belt |
| False-onset candidates (S₃≥20 mm but stall) | 3,408 across all cell-years (mean 1.12/cell-year, max 16) |
| Break runs | 11,902 (mean 3.9/cell-year); days flagged `break_active` 0.31 of post-onset days |
| Dry-spell runs | 6,487 (mean 2.13/cell-year); days flagged 0.16 of post-onset days |
| Revival events | 11,835 (0.99 per break run) |

Regional behavior is physically sensible: coastal/early cells (lat ≤ 12, W-Ghats side) show
early-June onset; inland MH/KN cells mid-to-late June; the TN rain-shadow interior triggers
only in August/September or shows no onset in deficit years (2015, 2019, 2023). 2019 — the
Indian monsoon drought year — shows the latest onsets and zero breaks for interior cells
(see examples below).

## 4. Worked label examples (real data)

### 4.1 False onset — interior TN `10.0_77.5`, 2019 (SW-monsoon drought year)
Onset only on **2019-09-15** after **6 stalled S₃≥20 mm candidates** earlier in JJAS
(pre-monsoon showers that did not sustain). The model's job in the demo scenario
(false-onset → dry-spell) is to NOT fire on these candidates and to quantify the
downside of sowing into an un-established monsoon.

| date | R (mm) | onset_active |
| --- | --- | --- |
| 2019-06-05 | 12.54 | 0 |
| 2019-06-06 … 06-24 | 0.00 | 0 |
| … 3 more unsustained S₃≥20 mm candidates … | — | 0 |
| 2019-09-15 | onset | 1 |

Same cell in 2016: onset 2016-07-27 after 3 false candidates; 2020: onset 2020-08-27 after 7;
2021: onset 2021-07-07 after 4. The outlier 2024 onset 2019-06-03 (0 false candidates) = an
exceptionally well-established June.

### 4.2 Break → revival → dry spell — interior TN `10.5_77.0`, 2015 (onset 2015-06-20)

| date | R (mm) | break_active | dry_spell_active | revival_day |
| --- | --- | --- | --- | --- |
| 2015-06-28 … 07-11 | < 1.0 | 1 (14 d break) | 1 (14 d dry spell) | 0 |
| 2015-07-12 | 2.87 | 0 | 0 | **1** |
| 2015-07-13 … 07-17 | < 1.8 | 1 (5 d break) | 0 | 0 |
| 2015-07-18 | 8.71 | 0 | 0 | **1** |
| 2015-07-19 … 07-22 | ≥ 2.7 | 0 | 0 | 0 |

This is a textbook **false-onset risk pattern**: onset fires on 06-20, then the cell gets
essentially 14 days of stress-level rain (<1 mm) — exactly the "sowing after a false onset,
then a dry spell" hazard the advisory system must warn about. Breaks run through
Jul 25–Aug 10, Aug 19–Sep 04 and Sep 09–24 (4 more breaks, 3 further dry spells).

### 4.3 No onset — `10.0_77.25` in 2016 & 2023 (`onset_date = None`, 5–6 false candidates)
SW-monsoon never establishes under the proxy → advisory module will treat the cell as
"onset still pending" all season and prioritize dry-sowing/wait advice rather than a
risk-neutral "sow" recommendation.

## 5. Outputs

| Artifact | Rows | Columns |
| --- | --- | --- |
| `data/processed/label_daily.parquet` | 370,880 (304×1220) | cell_id, date, year, doy, dseason, insufficient_data, onset_active, onset_date, break_active, dry_spell_active, revival_day, rain_mm |
| `data/processed/label_events.parquet` | 3,040 | cell_id, year, onset_date, no_onset, false_onset_candidates, n_breaks, n_dry_spells, missing_frac, insufficient_data |

Rebuild command: `python src/labels/build_labels.py`.

## 6. Assumptions & pending calibrations

1. **Thresholds are proxy defaults** (`CALIBRATION_PENDING`) — re-tune at the single source
   `src/labels/definitions.py` when MoES/village checklists arrive; never edit another copy.
2. **Onset is once-per-cell-year within JJAS June–Sep.** Late-onset cells (Sep) and no-onset
   cells are legitimate outcomes for the SW-monsoon window, not data errors.
3. **Break/dry-spell/dry events are post-onset only** (cropping-window semantics).
4. **JJAS-only trailing windows.** The 3-day trailing sum at day *t* uses days *inside* the
   JJAS window only (t−2..t ≥ Jun 1); pre-monsoon May rainfall never feeds the onset
   threshold (season-window semantics, as IMD declares onset within the season). Verified:
   `10.0_76.25` 2015 57.8 mm/3-d May-end burst produced no onset candidate.
5. `onset_active` is the day-of-onset boolean; the continuous `onset_date` column is a
   per-season attribute repeated daily — model features must never use `onset_date` at
   forecast time T when onset has not yet occurred (temporal non-anticipation verified in
   Phase D leakage audit).
6. Labels use the full season's rainfall to *date* events retrospectively; predictor
   features at day T use data ≤ T only (Phase D check L‑1 → L‑5).