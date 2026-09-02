"""Download NASA POWER daily meteorological data for the pilot bbox (regional API).

API constraints verified 2026-09-02 (HTTP 422 feedback from the server itself):
- max 1 parameter per request
- max 10 degree range in latitude per request
So we download one parameter at a time and split the lat range into <=10 deg bands.

Source: https://power.larc.nasa.gov/api/temporal/daily/regional
- 0.5x0.5 grid; daily; AG community; met from 1981 to NRT; NO auth required.

Parameters (daily, AG): T2M, T2M_DEW, T2M_MAX, T2M_MIN, PRECTOTCORR, PS, RH2M, WS2M, WS2M_MAX
Period: 2015-2024.
Region: pilot bbox, split into 2 lat bands.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from data_pipeline_utils import RAW, log_download, record_checksum  # noqa: E402

# API constraints verified 2026-09-02 (HTTP 422 from server):
#  - max 1 parameter per request
#  - latitude range must be >= 2 degrees and <= 10 degrees
# Valid daily AG parameter names (POWER docs): T2M, T2MDEW, T2MWET, T2M_MAX,
# T2M_MIN, RH2M, PS, WS10M, WS10M_MAX, PRECTOTCORR ...
OUT_DIR = RAW / "nasa"
BASE = "https://power.larc.nasa.gov/api/temporal/daily/regional"
PARAMS = [
    "T2M", "T2MDEW", "T2M_MAX", "T2M_MIN", "PRECTOTCORR",
    "PS", "RH2M", "WS10M", "WS10M_MAX",
]
# bbox lat 9.9..20.6 -> two bands each within [2,10] deg, on the 0.5 grid
LON_LO, LON_HI = 72.6, 80.9
LAT_BANDS = [(10.0, 20.0), (20.0, 22.0)]
YEARS = list(range(2015, 2025))
TRIALS = 3


def build_url(year: int, lat_min: float, lat_max: float, param: str) -> str:
    return (
        f"{BASE}?latitude-min={lat_min:.1f}&latitude-max={lat_max:.1f}"
        f"&longitude-min={LON_LO:.1f}&longitude-max={LON_HI:.1f}"
        f"&start={year}0101&end={year}1231"
        f"&parameters={param}&community=AG&format=CSV"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n_ok = n_fail = 0
    for param in PARAMS:
        for band_idx, (lat_min, lat_max) in enumerate(LAT_BANDS, start=1):
            for year in YEARS:
                dest = OUT_DIR / f"nasa_power_daily_{param}_b{band_idx}_{year}.csv"
                if dest.exists() and dest.stat().st_size > 1000:
                    n_ok += 1
                    continue
                url = build_url(year, lat_min, lat_max, param)
                ok = False
                for trial in range(1, TRIALS + 1):
                    try:
                        r = requests.get(url, timeout=180)
                        if r.status_code != 200 or len(r.text) < 1000:
                            print(f"[warn] {param} b{band_idx} {year} t{trial}: HTTP {r.status_code} len {len(r.text)}")
                            if '"errors"' in r.text or "failed" in r.text:
                                print(f"   server msg: {r.text[:200]}")
                            time.sleep(4)
                            continue
                        dest.write_text(r.text, encoding="utf-8")
                        record_checksum("nasa", dest, url)
                        log_download("nasa", url, dest, True)
                        n_ok += 1
                        ok = True
                        break
                    except Exception as e:  # noqa: BLE001
                        print(f"[err] {param} b{band_idx} {year} t{trial}: {e}")
                        time.sleep(4)
                if not ok:
                    n_fail += 1
                    log_download("nasa", url, dest, False, note="all trials failed")
                time.sleep(0.5)  # polite pacing
    print(f"NASA POWER complete: ok={n_ok} fail={n_fail}")


if __name__ == "__main__":
    main()