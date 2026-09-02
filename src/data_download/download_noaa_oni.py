"""Download NOAA CPC Oceanic Niño Index (ONI).

Source page VERIFIED 2026-09-02: https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/
- ONI v6: Niño 3.4 (5N-5S, 120-170W) 3-month running mean SST anomaly, ERSSTv5/v6.
- Coverage from 1950; full coverage of 2015-2024 expected.
Two files fetched when reachable; both are small text/CSV:
  1. ONI table (v6 page HTML)  -- kept for provenance
  2. oni.ascii.txt (standard ONI data file) -- kept when available
This script DOES NOT fabricate a file if the server 404s; it logs the failure.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_pipeline_utils import RAW, log_download, record_checksum, sha256_file  # noqa: E402

OUT_DIR = RAW / "noaa"
ONI_PAGE = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v6/"
ONI_TXT = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
HEADERS = {"User-Agent": "SIH2026-DataResearch/1.0"}


def fetch(url: str, dest: Path) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=60)
        if r.status_code != 200:
            print(f"[warn] {url} -> {r.status_code}")
            log_download("noaa", url, dest, False, note=f"HTTP {r.status_code}")
            return False
        if not r.text.strip():
            print(f"[warn] {url} empty body")
            return False
        dest.write_text(r.text, encoding="utf-8")
        print(f"[ok] {dest.name}: {len(r.text):,} chars")
        record_checksum("noaa", dest, url)
        log_download("noaa", url, dest, True)
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[err] {url}: {e}")
        log_download("noaa", url, dest, False, note=str(e))
        return False


def summarize(path: Path) -> None:
    """Print a quick ONI 2015-2024 coverage check from the ascii file if present."""
    if not path.exists():
        print("oni.ascii.txt unavailable - coverage summary skipped (server 404).")
        return
    years = sorted({int(m.group(1)) for m in re.finditer(r"^\s+\w{3}\s+(\d{4})\s", path.read_text(), re.M)})
    cover = [y for y in range(2015, 2025) if y in years]
    missing = [y for y in range(2015, 2025) if y not in years]
    print(f"ONI years on file: {min(years)}..{max(years)}")
    print(f"2015-2024 present: {len(cover)}/10  missing={missing or 'none'}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # 1) ONI page snapshot (HTML) for provenance / manual parse
    fetch(ONI_PAGE, OUT_DIR / "oni_v6_page.html")
    # 2) ONI data file
    p = OUT_DIR / "oni.ascii.txt"
    if p.exists():
        p.unlink()  # allow fresh fetch; record_checksum appends to ledger
    if fetch(ONI_TXT, p):
        summarize(p)


if __name__ == "__main__":
    main()