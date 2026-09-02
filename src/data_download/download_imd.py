"""Download IMD 0.25x0.25 daily gridded rainfall (yearly NetCDF files).

Source: IMD Pune (Pai et al. 2014, MAUSAM 65(1)).
Access pattern VERIFIED 2026-09-02:
  POST https://www.imdpune.gov.in/cmpg/Griddata/RF25.php  body={RF25: <year>}
  -> 200, Content-Type application/octet-stream, filename ind<year>_rfp25.nc (~25 MB/yr)

Period downloaded: 2015-01-01 .. 2024-12-31 (years 2015..2024).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_pipeline_utils import RAW, log_download, record_checksum, sha256_file  # noqa: E402

POST_URL = "https://www.imdpune.gov.in/cmpg/Griddata/RF25.php"
OUT_DIR = RAW / "imd"
YEARS = list(range(2015, 2025))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SIH2026-DataResearch/1.0",
    "Referer": "https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html",
}


def fetch_year(year: int, retries: int = 3) -> Path | None:
    out = OUT_DIR / f"ind{year}_rfp25.nc"
    if out.exists() and out.stat().st_size > 10_000_000:
        print(f"[skip] {year} already downloaded")
        return out
    for attempt in range(1, retries + 1):
        try:
            r = requests.post(POST_URL, data={"RF25": str(year)}, headers=HEADERS, timeout=120)
            if r.status_code != 200 or len(r.content) < 1_000_000:
                print(f"[warn] {year} attempt {attempt}: status={r.status_code} len={len(r.content)}")
                time.sleep(5)
                continue
            out.write_bytes(r.content)
            print(f"[ok] {year}: {len(r.content):,} bytes")
            return out
        except Exception as e:  # noqa: BLE001
            print(f"[err] {year} attempt {attempt}: {e}")
            time.sleep(5)
    return None


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n_ok = 0
    for y in YEARS:
        p = fetch_year(y)
        if not p:
            print(f"FAIL {y}")
            log_download("imd", POST_URL, Path("n/a"), False, note=f"year {y} download failed")
            continue
        record_checksum("imd", p, POST_URL)
        log_download("imd", POST_URL, p, True, note="yearly netcdf")
        n_ok += 1
        time.sleep(1)
    print(f"IMD complete: {n_ok}/{len(YEARS)} years")


if __name__ == "__main__":
    main()