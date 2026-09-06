"""Monsoon onset / break / revival / dry-spell label construction.

Each (cell, JJAS season) is processed independently: onset is declared once per
cell-year; break / dry-spell / revival are derived AFTER onset (cropping window).

Definitions implemented (see definitions.py for thresholds + CALIBRATION_PENDING
note on operational-proxy values):
  * onset       = first JJAS day t with 3-day trailing sum >=20 mm AND "sustained"
                  (>= 2.5 mm on at least one of t+1..t+2). Unsustained candidates
                  are recorded as false_onset_candidates (the "false onset" event
                  that the downscaled forecast must not fire on).
  * break       = run of >=5 consecutive days with rain < 2.5 mm, after onset.
  * revival_day = first day with rain >= 2.5 mm after a matured (>=5-day) break.
  * dry_spell   = run of >=7 consecutive days with rain < 1.0 mm, after onset.

Missing-data rule: if >10% of JJAS days in a cell-year are missing (valid==False)
the whole cell-year is marked insufficient_data and all labels = NaN. Missing days
inside a run are counted as "dry" (conservative: never shorten a dry/break run on
missing evidence) and documented as such.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.labels import definitions as D  # noqa: E402
from src.data_pipeline_utils import PROCESSED  # noqa: E402


def jjas_window(year: int) -> list[date]:
    out = []
    for mth, last in ((6, 30), (7, 31), (8, 31), (9, 30)):
        for day in range(1, last + 1):
            out.append(date(year, mth, day))
    return out


def _as_arrays(cy: pd.DataFrame, win: list[date]) -> tuple[np.ndarray, np.ndarray]:
    """Return (rain, valid) arrays aligned to the JJAS window."""
    cy = cy.set_index(pd.to_datetime(cy["date"]))
    idx = pd.to_datetime(pd.Series(win))
    rain = np.array([np.nan if np.isnan(x) else float(x)
                     for x in cy.loc[idx, "rain"].reindex(idx).values])
    valid = np.array(~np.isnan(rain))
    return rain, valid


def _sustained(rain: np.ndarray, valid: np.ndarray, t: int) -> bool:
    for k in (t + 1, t + 2):
        if k < len(rain):
            if valid[k] and rain[k] >= D.ONSET_SUSTAIN_MM:
                return True
    return False


def _runs_of_dry(rain: np.ndarray, valid: np.ndarray, thr: float,
                 start: int, min_len: int) -> list[tuple[int, int, int]]:
    """Runs (i_start, i_end_excl, length) of days with rain < thr, from `start`."""
    runs = []
    i = start
    n = len(rain)
    while i < n:
        if rain[i] < thr or not valid[i]:      # missing day counts as dry
            j = i
            while j < n and (rain[j] < thr or not valid[j]):
                j += 1
            if j - i >= min_len:
                runs.append((i, j, j - i))
            i = j
        else:
            i += 1
    return runs


def labels_for_cell_year(cy: pd.DataFrame, year: int) -> dict:
    win = jjas_window(year)
    rain, valid = _as_arrays(cy, win)
    n = len(win)
    missing_frac = 1.0 - valid.mean()
    insufficient = missing_frac > D.MISSING_FRAC_TOLERENCE

    onset_day = np.nan
    false_cands = []
    if not insufficient:
        s3 = np.full(n, np.nan)
        for t in range(2, n):
            if valid[t - 2] and valid[t - 1] and valid[t]:
                s3[t] = rain[t - 2] + rain[t - 1] + rain[t]
        cands = np.argwhere(s3 >= D.ONSET_SUM_MM).ravel()
        for t in cands:
            if not (_sustained(rain, valid, t)):
                false_cands.append(t)
                continue
            onset_day = t
            break
    onset_idx = int(onset_day) if np.isfinite(onset_day) else None

    break_runs = _runs_of_dry(rain, valid, D.BREAK_MM,
                              onset_idx if onset_idx is not None else n, D.BREAK_MIN_DAYS)
    dry_runs = _runs_of_dry(rain, valid, D.DRY_SPELL_MM,
                            onset_idx if onset_idx is not None else n, D.DRY_SPELL_MIN_DAYS)

    break_active = np.zeros(n, dtype=np.int8)
    for (i, j, _) in break_runs:
        break_active[i:j] = 1
    dry_active = np.zeros(n, dtype=np.int8)
    for (i, j, _) in dry_runs:
        dry_active[i:j] = 1

    revival = np.zeros(n, dtype=np.int8)
    for (i, j, _) in break_runs:
        k = j
        while k < n and not (valid[k] and rain[k] >= D.REVIVAL_MM):
            k += 1
        if k < n:
            revival[k] = 1
        else:
            pass   # no revival by season end

    return {
        "year": year, "win": win, "rain": rain, "valid": valid,
        "insufficient": insufficient, "missing_frac": float(missing_frac),
        "onset_idx": onset_idx, "onset_date": win[onset_idx] if onset_idx is not None else None,
        "false_cands": [win[t] for t in false_cands],
        "break_runs": [(win[i], win[j - 1], ln) for (i, j, ln) in break_runs],
        "dry_runs": [(win[i], win[j - 1], ln) for (i, j, ln) in dry_runs],
        "break_active": break_active, "dry_active": dry_active,
        "revival_day": revival,
    }


def build_label_tables(imd: pd.DataFrame, cells: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (daily_labels, events) long frames."""
    recs_daily, recs_evt = [], []
    for (cid, yr), cy in imd.groupby(["cell_id", "year"]):
        res = labels_for_cell_year(cy, yr)
        for i, d in enumerate(res["win"]):
            outer = res["insufficient"]
            recs_daily.append({
                "cell_id": cid, "date": d, "year": yr, "doy": d.timetuple().tm_yday,
                "dseason": i + 1,
                "insufficient_data": outer,
                "onset_active": np.nan if outer else (1 if i == res["onset_idx"] else 0),
                "onset_date": res["onset_date"],
                "break_active": np.nan if outer else int(res["break_active"][i]),
                "dry_spell_active": np.nan if outer else int(res["dry_active"][i]),
                "revival_day": np.nan if outer else int(res["revival_day"][i]),
                "rain_mm": res["rain"][i],
            })
        recs_evt.append({
            "cell_id": cid, "year": yr,
            "onset_date": res["onset_date"],
            "no_onset": res["onset_idx"] is None and not res["insufficient"],
            "false_onset_candidates": len(res["false_cands"]),
            "n_breaks": len(res["break_runs"]),
            "n_dry_spells": len(res["dry_runs"]),
            "missing_frac": res["missing_frac"],
            "insufficient_data": res["insufficient"],
        })
    daily = pd.DataFrame(recs_daily)
    events = pd.DataFrame(recs_evt)
    return daily, events


if __name__ == "__main__":
    import load
    imd = load.imd_series()
    cells = load.select_pilot_cells(imd)
    imd["year"] = pd.to_datetime(imd["date"]).dt.year
    imd = imd[imd["cell_id"].isin(cells.cell_id)]
    daily, events = build_label_tables(imd, cells)
    daily.to_parquet(PROCESSED / "label_daily.parquet")
    events.to_parquet(PROCESSED / "label_events.parquet")
    print("daily rows:", len(daily), " events rows:", len(events))
    print(daily[daily.onset_active == 1][["cell_id", "date"]].head(12).to_string(index=False))
    print("counts (strict post-onset):")
    print(daily.groupby("year")[["onset_active", "break_active",
                                 "dry_spell_active", "revival_day"]].sum().to_string())
    print("events describe:", events[["no_onset", "false_onset_candidates",
                                      "n_breaks", "n_dry_spells"]].describe().to_string())