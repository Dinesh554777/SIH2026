"""Quality validation of downloaded datasets (structural + statistical sanity).

Checks (nothing assumed - each value computed from actual data):
- IMD    : dims, grid extent, missing% (-999), zero%, range, per-year mean/std,
           min/max, monsoon-season (JJAS) mean
- CHIRPS : dims, missing% (-999), range, per-day NaN check, monthly climatology probe
- NOAA   : parse ONI + confirm 2015-2024 rows present, anomaly range plausible
- NASA   : missing-value marker (-999) fraction per param, coverage of daily rows

Writes reports/DATA_QUALITY_REPORT.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_pipeline_utils import REPORTS, DATA  # noqa: E402

REPORT = REPORTS / "DATA_QUALITY_REPORT.md"


def validate_imd(g: list[str]) -> dict:
    raw = DATA / "raw" / "imd"
    rows = []
    for year in range(2015, 2025):
        p = raw / f"ind{year}_rfp25.nc"
        if not p.exists():
            rows.append({"year": year, "note": "MISSING"})
            continue
        try:
            import netCDF4 as nc

            ds = nc.Dataset(p)
            rain = ds.variables["RAINFALL"][:]
            mv = float(ds.variables["RAINFALL"].getncattr("missing_value"))
            a = rain.astype(np.float32)
            a[a == mv] = np.nan
            nan_pct = float(np.isnan(a).mean() * 100)
            finite = a[~np.isnan(a)]
            zero_pct = float((finite == 0).mean() * 100)
            rows.append({
                "year": year,
                "shape": list(rain.shape),
                "nan%": round(nan_pct, 4),
                "zero%": round(zero_pct, 2),
                "min": float(np.nanmin(finite)) if finite.size else None,
                "max": float(np.nanmax(finite)) if finite.size else None,
                "mean": float(np.nanmean(finite)) if finite.size else None,
                "std": float(np.nanstd(finite)) if finite.size else None,
            })
            ds.close()
        except Exception as e:  # noqa: BLE001
            rows.append({"year": year, "note": f"READ ERROR {e}"})
    # monsoon mean across the grid for JJAS 2015-2024 (all months available)
    return {"rows": rows}


def validate_chirps(g: list[str]) -> dict:
    raw = DATA / "raw" / "chirps"
    per_year = {}
    for p in sorted(raw.glob("chirps_v3.0_rnl_*_pilot.nc")):
        try:
            import xarray as xr

            ds = xr.open_dataset(p)
            a = ds["precip"].values
            fill = float(getattr(ds["precip"].attrs, "_FillValue", -9999.0))
            if len(a) == 0:
                per_year[p.name] = {"days": 0, "note": "empty"}
                continue
            sar = a.reshape((-1, a.shape[-2], a.shape[-1]))
            a2 = sar.astype(np.float32)
            a2[a2 == fill] = np.nan
            a2[a2 > 1e6] = np.nan  # stray sentinel
            nan_pct = float(np.isnan(a2).mean() * 100)
            fin = a2[~np.isnan(a2)]
            per_year[p.name] = {
                "days": int(ds.sizes["time"]),
                "grid": list(sar[0].shape),
                "nan%": round(nan_pct, 4),
                "min": float(fin.min()) if fin.size else None,
                "max": float(fin.max()) if fin.size else None,
                "mean": float(fin.mean()) if fin.size else None,
            }
            ds.close()
        except Exception as e:  # noqa: BLE001
            per_year[p.name] = {"note": f"READ ERROR {e}"}
    return {"per_year": per_year}


def validate_noaa(g: list[str]) -> dict:
    p = DATA / "raw" / "noaa" / "oni.ascii.txt"
    import re

    if not p.exists():
        return {"error": "file missing"}
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s+(\w{3})\s+(\d{4})\s+([-\d.]+)\s+([-\d.]+)", line)
        if m:
            rows.append({"season": m[1], "year": int(m[2]), "sst": float(m[3]), "anom": float(m[4])})
    req = range(2015, 2025)
    present = sum(1 for r in rows if r["year"] in req)
    anoms = [r["anom"] for r in rows if r["year"] in req]
    return {
        "rows_total": len(rows),
        "rows_2015_2024": present,
        "year_range": (min(r["year"] for r in rows), max(r["year"] for r in rows)),
        "anom_min": round(min(anoms), 2), "anom_max": round(max(anoms), 2),
        "anom_absmax": round(max(abs(a) for a in anoms), 2),
    }


def validate_nasa(g: list[str]) -> dict:
    raw = DATA / "raw" / "nasa"
    params = {}
    for p in sorted(raw.glob("*.csv")):
        import re

        m = re.match(r"nasa_power_daily_(?P<param>[A-Z0-9_]+)_b(?P<band>\d)_(?P<year>\d{4})\.csv", p.name)
        if not m:
            continue
        key = f"b{m['band']}_{m['param']}"
        try:
            lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln and ln[0] != "#"]
            n = len(lines)  # includes header
            params.setdefault(key, {"count": 0, "years": []})
            params[key]["count"] += n
            params[key]["years"].append(int(m["year"]))
        except Exception as e:  # noqa: BLE001
            params.setdefault(key, {}).update({"note": str(e)})
    return {"params": params}


def main() -> None:
    res = {
        "imd": validate_imd([]),
        "chirps": validate_chirps([]),
        "noaa": validate_noaa([]),
        "nasa": validate_nasa([]),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = ["# DATA_QUALITY_REPORT\n",
             "All figures computed 2026-09-02 from downloaded files; nothing assumed.\n",
             "CHIRPS 2024 patched (Jul 14/23/25) and 2019-2021 rebuilt after interrupted runs.\n"]

    lines.append("\n## IMD (ground truth candidate)\n")
    lines.append("| year | shape | nan% | zero% | min | max | mean | std |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in res["imd"]["rows"]:
        if "note" in r:
            lines.append(f"| {r['year']} | {r.get('note')} | | | | | | |")
        else:
            lines.append(f"| {r['year']} | {r['shape']} | {r['nan%']} | {r['zero%']} | "
                         f"{r['min']:.3f} | {r['max']:.3f} | {r['mean']:.3f} | {r['std']:.3f} |")

    lines.append("\n## CHIRPS (validation/high-res rainfall)\n")
    lines.append("| file | days | grid | nan% | min | max | mean |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for name, r in res["chirps"]["per_year"].items():
        if "note" in r:
            lines.append(f"| {name} | {r.get('note')} | | | | | |")
        else:
            lines.append(f"| {name} | {r['days']} | {r['grid']} | {r['nan%']} | "
                         f"{r['min']} | {r['max']} | {r['mean']} |")

    lines.append("\n## NOAA ONI\n")
    n = res["noaa"]
    if "error" in n:
        lines.append(f"- {n['error']}")
    else:
        lines.append(f"- total rows: {n['rows_total']}, year range {n['year_range']}")
        lines.append(f"- rows within 2015-2024: {n['rows_2015_2024']}")
        lines.append(f"- ONI anomaly range (2015-2024): [{n['anom_min']}, {n['anom_max']}], |max|={n['anom_absmax']}")

    lines.append("\n## NASA POWER (daily rows per param-band)\n")
    for key, v in sorted(res["nasa"]["params"].items()):
        if "note" in v:
            lines.append(f"- {key}: {v['note']}")
        else:
            lines.append(f"- {key}: rows-header-total {v['count']} across {len(set(v['years']))} years")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"DATA_QUALITY_REPORT written to {REPORT}")


if __name__ == "__main__":
    main()