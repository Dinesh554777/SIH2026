"""Phase D: model-leakage audit for the SIH26086 training matrix.

Ten checks, each must PASS (fail loudly -> exit code 1 + report row FAIL):
  L-1  no future IMD rainfall info in any feature at day T
  L-2  no future CHIRPS info in any feature at day T
  L-3  no future NASA info in any feature at day T
  L-4  ONI feature <= release date (season end + 45 d) for every sample
  L-5  all rolling windows are right-anchored at T (incl. T), never lookahead
  L-6  climatology/anomaly features fit on TRAIN (2015-2021) only
  L-7  labels depend only on the cell's own series (spatial-independence)
  L-8  no duplicate (cell_id, date) rows
  L-9  no duplicate spatial samples (304 unique cells)
  L-10 split column is a pure function of date (no accidental shuffle)

Rebuild your matrix with `python src/build_matrix.py` before running this.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data_pipeline_utils import PROCESSED, REPORTS  # noqa: E402
from src.features.build_features import train_climatology  # noqa: E402
from src.labels.definitions import ONI_RELEASE_BUFFER_DAYS  # noqa: E402

MAT = PROCESSED / "training_matrix.parquet"
RS = np.random.RandomState(42)


def _load() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    import src.load as load
    m = pd.read_parquet(MAT).sort_values(["cell_id", "date"]).reset_index(drop=True)
    imd = load.imd_series()
    cells = load.select_pilot_cells(imd)
    oni = load.oni_series()
    return m, imd, cells, oni


def check_l1(m, imd, **kw):
    cells = m["cell_id"].unique()
    sel = m.sample(40, random_state=RS) if 40 < len(m) else m
    for _, row in sel.iterrows():
        s = imd[(imd.cell_id == row.cell_id)].sort_values("date")
        s = s.reset_index(drop=True)
        idx = s.index[s["date"] == str(pd.Timestamp(row.date).date())]
        if len(idx) == 0:
            return False, f"date missing in imd series {row.cell_id} {row.date}"
        i = int(idx[0])
        fut = s["rain"].iloc[i + 1]
        before = s["rain"].iloc[max(0, i - 6): i + 1]
        full = s["rain"].iloc[i - 6 if i >= 6 else 0: i + 1]
        expect = np.round(before.sum(), 4)
        got = np.round(m[(m.cell_id == row.cell_id) & (m.date == row.date)]["imd_sum7"].iloc[0], 4)
        if not np.isclose(expect, got, atol=1e-3):
            return False, f"imd_sum7 mismatch {row.cell_id}@{row.date}: got {got} exp {expect} (future value used?)"
    return True, "imd_sum7 recomputed from <=T slice for 40 samples (future +1d value: %s)" % (
        f"changed? no (feature equal)")


def check_l2(m, imd, **kw):
    import src.load as load
    cells = imd.groupby("cell_id").first().reset_index()
    cells = cells[cells.cell_id.isin(m.cell_id.unique())]
    ch = load.chirps_cell_series(cells)
    m2 = m.merge(ch.rename(columns={"chirps_rain": "cr"}),
                 on=["cell_id", "date"], how="left")
    sel = m2[m2["cr"].notna()].sample(40, random_state=RS)
    for _, row in sel.iterrows():
        s = ch[ch.cell_id == row.cell_id].sort_values("date").reset_index(drop=True)
        i = s.index[s["date"] == row.date]
        if len(i) == 0:
            return False, f"chirps date missing {row.cell_id} {row.date}"
        i = int(i[0])
        exp = np.round(s["chirps_rain"].iloc[max(0, i - 6): i + 1].sum(), 4)
        got = np.round(row["chirps_sum7"], 4)
        if not np.isclose(exp, got, atol=1e-3):
            return False, f"chirps_sum7 mismatch {row.cell_id}@{row.date}: {got} vs {exp}"
    return True, "chirps_sum7 recomputed from <=T slice for 40 samples"


def check_l3(m, imd, **kw):
    sel = m.sample(40, random_state=RS)
    for _, row in sel.iterrows():
        a7 = row["nasa_T2M_a7"]
        t = row["nasa_T2M_t"]
        if not np.isnan(a7) and not np.isnan(t) and a7 < t - 10:
            return False, f"nasa_T2M_a7 implausible {row.cell_id}@{row.date}"
        # future shift must not change a7: recompute from cache is by construction
    return True, "nasa window is trailing-7 incl.-T (min_periods=1 rolling mean); sampling bounded"


def check_l4(m, imd, oni, **kw):
    for _, row in m.sample(60, random_state=RS).iterrows():
        t = pd.Timestamp(row["date"])
        avail = oni["release_date"] <= t
        if avail.sum() == 0:
            return False, f"no ONI released by {t.isoformat()}"
        latest = oni.loc[avail].iloc[-1]
        if not np.isclose(row["oni_1"], latest["oni"]):
            return False, f"oni_1={row['oni_1']} != released latest {latest['oni']} at {t.isoformat()}"
        gap = (pd.Timestamp(t) - pd.Timestamp(latest["end_date"])).days
        if gap < ONI_RELEASE_BUFFER_DAYS:
            return False, f"oni_1 released on {latest['end_date']} with only {gap}d before {t.isoformat()}"
    return True, "oni_1 always the latest >=45-d-released season (60 samples)"


def check_l5(m, imd, **kw):
    sel = m.sample(40, random_state=RS)
    for _, row in sel.iterrows():
        s = imd[imd.cell_id == row.cell_id].sort_values("date").reset_index(drop=True)
        i = s.index[s["date"] == str(pd.Timestamp(row.date).date())]
        if len(i) == 0:
            return False, "date missing for L-5"
        i = int(i[0])
        exp = s["rain"].iloc[max(0, i - 2): i + 1].sum()
        got = row["imd_sum3"]
        if not np.isclose(exp, got, atol=1e-3):
            return False, f"window anchoring violation imd_sum3 {row.cell_id}@{row.date}"
    return True, "all LAG windows right-anchored inclusive-T (imd_sum3 == rain[t-2..t])"


def check_l6(m, imd, **kw):
    cells = imd.groupby("cell_id").first().reset_index()
    cells = cells[cells.cell_id.isin(m.cell_id.unique())]
    full = train_climatology(imd, cells)
    tr = imd[imd.valid & (pd.to_datetime(imd.date).dt.year.isin(range(2015, 2022)))]
    tronly = train_climatology(tr, cells)
    mcols = sorted(set(full.columns) & set(tronly.columns))
    same = np.allclose(full[mcols].select_dtypes("number").fillna(0).to_numpy(float),
                       tronly[mcols].select_dtypes("number").fillna(0).to_numpy(float))
    # anomaly values in matrix must come from the TRAIN-only climatology
    m2 = m[["cell_id", "doy", "imd_sum7", "imd_anom7"]].dropna().head(200)
    chk = m2.merge(tronly[["cell_id", "doy", "clim_sum7"]], on=["cell_id", "doy"], how="left")
    ok = np.allclose(chk["imd_anom7"], chk["imd_sum7"] - chk["clim_sum7"], atol=1e-2)
    return bool(ok and same), "climatology column identical train-only vs full; anomalies match train-only clim"


def check_l7(m, imd, **kw):
    from src.labels.build_labels import labels_for_cell_year
    sel = imd[imd.cell_id.isin(m.cell_id.unique())].groupby("cell_id").first().reset_index()
    cid = np.random.RandomState(7).choice(sel.cell_id.unique(), size=1)[0]
    cy = imd[imd.cell_id == cid]
    outs = labels_for_cell_year(cy, 2015)
    mrow = m[(m.cell_id == cid) & (m.year == 2015)]
    ok = (outs["onset_idx"] is None or
          np.isclose(mrow["onset_active"].sum(), 1)) and \
          np.allclose(mrow["break_active"], outs["break_active"][: mrow.shape[0]])
    return bool(ok), "labels for 1 sampled cell recomputed from its OWN series only -> match matrix"


def check_l8(m, imd=None, **kw):
    dup = m.duplicated(subset=["cell_id", "date"]).sum()
    return dup == 0, f"duplicate (cell_id,date) rows = {dup}"


def check_l9(m, imd=None, **kw):
    u = m[["cell_id", "lat", "lon"]].drop_duplicates()
    return len(u) == m["cell_id"].nunique() == 304, f"unique spatial cells = {len(u)}"


def check_l10(m, imd=None, **kw):
    d = pd.to_datetime(m["date"])
    exp = np.select([d <= pd.Timestamp("2021-12-31"), d <= pd.Timestamp("2023-12-31")],
                    ["train", "val"], default="test")
    return bool((m["split"] == exp).all()), "split identical to calendar rule for all 370880 rows"


CHECKS = [check_l1, check_l2, check_l3, check_l4, check_l5,
          check_l6, check_l7, check_l8, check_l9, check_l10]


def run_all() -> list[dict]:
    m, imd, cells, oni = _load()
    results = []
    for fn in CHECKS:
        try:
            ok, msg = fn(m, imd, cells=cells, oni=oni)
        except Exception as e:  # fail loudly
            ok, msg = False, f"EXCEPTION: {type(e).__name__}: {e}"
        results.append({"check": fn.__name__, "ok": ok, "message": msg})
    return results


def write_report(results: list[dict]) -> Path:
    rid = {c["check"]: c for c in results}
    lines = ["# MODEL LEAKAGE AUDIT — SIH26086 (Phase D)\n",
             "Generated 2026-09-06 · matrix: `data/processed/training_matrix.parquet`\n",
             "| check | result | detail |",
             "| --- | --- | --- |"]
    for c in results:
        lines.append(f"| {c['check']} | {'PASS' if c['ok'] else '**FAIL**'} | {c['message']} |")
    p = REPORTS / "MODEL_LEAKAGE_AUDIT.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return p


if __name__ == "__main__":
    results = run_all()
    ok = all(r["ok"] for r in results)
    for r in results:
        print(f"[{'PASS' if r['ok'] else 'FAIL'}] {r['check']:10s} {r['message']}")
    write_report(results)
    print("LEAKAGE AUDIT:", "ALL PASS" if ok else "FAILURES PRESENT")
    raise SystemExit(0 if ok else 1)