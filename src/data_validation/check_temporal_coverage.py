"""Temporal coverage check for downloaded datasets vs required period 2015-01-01..2024-12-31.

Datasets checked:
- IMD    : yearly netCDF (data/raw/imd/ind<year>_rfp25.nc)  - per-file year coverage
- CHIRPS : yearly pilot netCDF (data/raw/chirps/chirps_v3.0_rnl_<year>_pilot.nc)
- NOAA   : oni.ascii.txt (3-month seasons)
- NASA   : per-param/band/year CSVs (each file covers one full calendar year)

No values are invented: every conclusion derives from the actual downloaded files.
Writes reports/COVERAGE_REPORT.md and prints a machine-readable summary.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_pipeline_utils import REPORTS, DATA  # noqa: E402

REQUIRED = (date(2015, 1, 1), date(2024, 12, 31))
REPORT = REPORTS / "COVERAGE_REPORT.md"


def _days_in_year(y: int) -> int:
    return 366 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 365


def check_imd() -> dict:
    raw = DATA / "raw" / "imd"
    rows = []
    for year in range(REQUIRED[0].year, REQUIRED[1].year + 1):
        p = raw / f"ind{year}_rfp25.nc"
        if not p.exists():
            rows.append({"year": year, "present": False, "days": 0, "note": "file missing"})
            continue
        try:
            import netCDF4 as nc

            ds = nc.Dataset(p)
            t = ds.variables["TIME"]
            from cftime import num2date

            times = num2date(t[:], t.units, calendar=getattr(t, "calendar", "standard"))
            # day-of-year span of this file
            first, last = times[0], times[-1]
            req_days = _days_in_year(year)
            got_days = len(times)
            status = "OK" if got_days == req_days else "PARTIAL_COVERAGE"
            rows.append({
                "year": year, "present": True, "days": got_days, "expected": req_days,
                "first": str(first), "last": str(last), "note": status,
            })
            ds.close()
        except Exception as e:  # noqa: BLE001
            rows.append({"year": year, "present": True, "days": -1, "note": f"read error: {e}"})
    missing_years = [r["year"] for r in rows if not r["present"]]
    partial = [r["year"] for r in rows if r.get("first") and r["note"] != "OK"]
    return {"rows": rows, "missing_years": missing_years, "partial": partial,
            "status": "PARTIAL_COVERAGE" if (missing_years or partial) else "FULL_COVERAGE"}


def check_chirps() -> dict:
    raw = DATA / "raw" / "chirps"
    missing_years, partial, days_info, times = [], [], [], []
    for year in range(REQUIRED[0].year, REQUIRED[1].year + 1):
        p = raw / f"chirps_v3.0_rnl_{year}_pilot.nc"
        if not p.exists():
            missing_years.append(year)
            continue
        try:
            import xarray as xr

            ds = xr.open_dataset(p)
            n = int(ds.sizes["time"])
            first = str(ds.time.values[0])[:10]
            last = str(ds.time.values[-1])[:10]
            gaps = n - _days_in_year(year)
            status = "OK" if gaps == 0 else "PARTIAL_COVERAGE"
            if gaps != 0:
                partial.append({year: n})
            days_info.append({"year": year, "days": n, "first": first, "last": last, "note": status})
            ds.close()
        except Exception as e:  # noqa: BLE001
            missing_years.append(year)
            print(f"  [chirps] {year} read error: {e}")
    status = "PARTIAL_COVERAGE" if (missing_years or partial) else "FULL_COVERAGE"
    return {"days_info": days_info, "missing_years": missing_years,
            "partial": partial, "status": status}


def check_noaa() -> dict:
    p = DATA / "raw" / "noaa" / "oni.ascii.txt"
    import re

    years = []
    if p.exists():
        years = sorted({int(m.group(1)) for m in re.finditer(
            r"^\s+\w{3}\s+(\d{4})\s", p.read_text(encoding="utf-8"), re.M)})
    req = set(range(REQUIRED[0].year, REQUIRED[1].year + 1))
    missing = sorted(req - set(years))
    status = "FULL_COVERAGE" if not missing else "PARTIAL_COVERAGE"
    return {"years_on_file": (min(years), max(years)) if years else None,
            "missing_years": missing, "status": status,
            "note": "3-month seasonal index; ONI year presence checked"}


def check_nasa() -> dict:
    raw = DATA / "raw" / "nasa"
    files = sorted(raw.glob("nasa_power_daily_*.csv"))
    # unique (param,band) combos
    import re

    combos = {}
    for f in files:
        m = re.match(r"nasa_power_daily_(?P<param>[A-Z0-9_]+)_b(?P<band>\d)_(?P<year>\d{4})\.csv", f.name)
        if not m:
            continue
        ckey = (m["param"], m["band"])
        combos.setdefault(ckey, []).append(int(m["year"]))
    req = set(range(REQUIRED[0].year, REQUIRED[1].year + 1))
    issues = []
    for ckey, yrs in combos.items():
        miss = sorted(req - set(yrs))
        if miss:
            issues.append((ckey, miss))
    status = "PARTIAL_COVERAGE" if issues else "FULL_COVERAGE"
    return {"file_count": len(files), "combos": len(combos), "issues": issues, "status": status}


def main() -> None:
    results = {
        "required_period": [REQUIRED[0].isoformat(), REQUIRED[1].isoformat()],
        "imd": check_imd(),
        "chirps": check_chirps(),
        "noaa": check_noaa(),
        "nasa": check_nasa(),
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    lines = ["# COVERAGE_REPORT\n", f"**Required period:** {results['required_period'][0]} .. {results['required_period'][1]}\n"]
    for ds in ("imd", "chirps", "noaa", "nasa"):
        r = results[ds]
        lines.append(f"\n## {ds.upper()} — status: **{r['status']}**\n")
        if ds == "imd":
            lines.append("| year | days | first | last | note |")
            lines.append("| --- | --- | --- | --- | --- |")
            for row in r["rows"]:
                lines.append(f"| {row['year']} | {row.get('days','')} | {row.get('first','')} | {row.get('last','')} | {row['note']} |")
        elif ds == "chirps":
            lines.append("| year | days | first | last | note |")
            lines.append("| --- | --- | --- | --- | --- |")
            for row in r["days_info"]:
                lines.append(f"| {row['year']} | {row['days']} | {row['first']} | {row['last']} | {row['note']} |")
        elif ds == "noaa":
            lines.append(f"- years on file: {r['years_on_file']}")
            lines.append(f"- missing: {r.get('missing_years') or 'none'}")
            lines.append(f"- {r.get('note','')}")
        else:
            lines.append(f"- files: {r['file_count']}, (param,band) combos: {r['combos']}")
            lines.append(f"- gaps: {r['issues'] or 'none'}")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"COVERAGE_REPORT written to {REPORT}")
    for ds in ("imd", "chirps", "noaa", "nasa"):
        print(f"  {ds}: {results[ds]['status']}")


if __name__ == "__main__":
    main()