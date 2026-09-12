"""Official IMD 0.25° daily gridded rainfall client (Gate J1).

Uses the IMD Pune operational access pattern VERIFIED by this project on
2026-09-02 (see src/data_download/download_imd.py):

    POST https://www.imdpune.gov.in/cmpg/Griddata/RF25.php   body {RF25: <year>}
    -> 200, application/octet-stream, yearly NetCDF ind<year>_rfp25.nc

The client downloads the NetCDF for the target year, parses it with netCDF4
(the SAME reader semantics as src.load.imd_series), and extracts the latest
completed observation day for the registered pilot cells.

Integrity guarantees:
- Historical files under data/raw/imd are NEVER read here; only an http(s) URL
  (configurable via LIVE_SOURCE_URL) is used. Local paths are rejected.
- No fabricated data: if the endpoint is unreachable or the target day is absent,
  the client raises SourceUnavailableError with the actual technical reason.
- rainfall units are explicit mm/day; values are pre-validated later by the
  normalizer (missing -> NaN is passed through as a row with rainfall=None).
"""

from __future__ import annotations

import os
import tempfile
from datetime import date as date_t, datetime, timezone

import numpy as np
import pandas as pd
import requests

from src.ingestion.clients.base import ObservationSource, SourceResponse
from src.ingestion.errors import ConfigurationError, SourceUnavailableError
from src.ingestion.validators import target_observation_date

# Verified IMD Pune operational distribution endpoint.
DEFAULT_IMD_POST_URL = "https://www.imdpune.gov.in/cmpg/Griddata/RF25.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SIH2026-LiveIngest/1.0",
    "Referer": "https://www.imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html",
}

MIN_PAID = 1_000_000  # a valid yearly IMD file is ~25 MB; anything tiny is an error page


class IMDGridSource(ObservationSource):
    name = "imd"
    is_mock = False

    def __init__(self, cells: pd.DataFrame, url: str | None = None,
                 timeout: float = 30.0, post_url: str | None = None):
        if url is not None and not (url.startswith("https://") or url.startswith("http://")):
            raise ConfigurationError(
                "IMD source URL must be http(s); local files are not a live source")
        self.post_url = (url or post_url or DEFAULT_IMD_POST_URL)
        self.timeout = float(timeout)
        self.cells = cells[["cell_id", "lat", "lon"]].drop_duplicates().reset_index(drop=True)

    # ------------------------------------------------------------------ fetch
    def fetch(self, now: datetime | None = None) -> SourceResponse:
        now = now or datetime.now(timezone.utc)
        target = target_observation_date(now, lookback_hours=24.0)
        year = int(target.year)
        url = self.post_url
        try:
            r = requests.post(url, data={"RF25": str(year)}, headers=HEADERS,
                              timeout=self.timeout)
        except requests.RequestException as exc:
            raise SourceUnavailableError(
                f"IMD HTTP request failed (source={url}, year={year}): "
                f"{type(exc).__name__}: {exc}") from exc

        if r.status_code != 200 or len(r.content) < MIN_PAID:
            raise SourceUnavailableError(
                f"IMD returned status={r.status_code} bytes={len(r.content)} "
                f"for year={year} (source={url}); content-length too small for a "
                f"valid IMD rainfall NetCDF")

        rows = self._parse_netcdf(r.content, year, target)
        if not rows:
            raise SourceUnavailableError(
                f"IMD {year} file does not contain target observation day {target}")

        return SourceResponse(
            source=self.name,
            rows=rows,
            retrieved_at=now,
            metadata={
                "url": url,
                "year": year,
                "observation_date": target.isoformat(),
                "coverage": f"{len(rows)}/{len(self.cells)} pilot cells",
                "version": f"imd_rfp25_{year}",
            },
        )

    # ---------------------------------------------------------------- parsing
    def _parse_netcdf(self, payload: bytes, year: int,
                      target: date_t) -> list[dict]:
        import netCDF4 as nc

        with tempfile.NamedTemporaryFile(suffix=".nc", delete=False) as tmp:
            tmp.write(payload)
            tmp_path = tmp.name
        try:
            ds = nc.Dataset(tmp_path, "r")
            try:
                lats = ds.variables["LATITUDE"][:].astype(float)
                lons = ds.variables["LONGITUDE"][:].astype(float)
                rain = np.ma.filled(ds.variables["RAINFALL"][:], np.nan).astype(float)
                # find the time index for the target date
                tvals = ds.variables["TIME"][:]
                units = ds.variables["TIME"].units
                calendar = getattr(ds.variables["TIME"], "calendar", "standard")
                from cftime import num2date

                times = [str(x)[:10] for x in
                         num2date(tvals, units, calendar=calendar)]
                try:
                    ti = times.index(str(target))
                except ValueError:
                    return []
                rows = []
                for _, c in self.cells.iterrows():
                    li = _nearest(lats, float(c["lat"]))
                    lo = _nearest(lons, float(c["lon"]))
                    if li is None or lo is None:
                        continue  # cell centre not on this year's grid
                    v = float(rain[ti, li, lo])
                    value = None if (v != v) else v  # NaN -> missing
                    rows.append({
                        "cell_id": str(c["cell_id"]),
                        "lat": float(c["lat"]),
                        "lon": float(c["lon"]),
                        "observation_time": datetime(
                            year, target.month, target.day, tzinfo=timezone.utc),
                        "rainfall": value,
                    })
                return rows
            finally:
                ds.close()
        except Exception as exc:
            raise SourceUnavailableError(
                f"IMD NetCDF parse failed: {type(exc).__name__}: {exc}") from exc
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    # ---------------------------------------------------------------- metadata
    def describe(self) -> dict:
        return {
            "name": self.name,
            "product": "IMD 0.25x0.25 daily gridded rainfall (rfp25, Pai et al. 2014)",
            "method": "POST RF25.php {RF25=<year>} -> yearly NetCDF (project-verified 2026-09-02)",
            "url": self.post_url,
            "units": "mm/day",
            "is_mock": False,
            "note": "Primary rainfall source consistent with the frozen scientific validation.",
        }


def _nearest(values: np.ndarray, target: float) -> int | None:
    """Index of an exact grid value (tol 1e-6), else None."""
    i = int(np.searchsorted(values, target))
    for idx in (i - 1, i, i + 1):
        if 0 <= idx < len(values) and abs(float(values[idx]) - float(target)) < 1e-6:
            return idx
    return None