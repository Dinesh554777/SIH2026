"""Deterministic MOCK / TEST-ONLY observation source (Gate J1).

This source MUST never be used in production live mode. It is used only by the
automated test suite (and by operators who explicitly set LIVE_ALLOW_MOCK=1) so
that no automated test ever depends on Internet access.

It returns realistic mm/day values for the entire registered pilot grid for a
fixed observation day; the value is a pure deterministic function of
(cell_id, observation_date) so runs are reproducible byte-for-byte.
"""

from __future__ import annotations

import hashlib
from datetime import date as date_t, datetime, timezone

import pandas as pd

from src.ingestion.clients.base import ObservationSource, SourceResponse
from src.ingestion.validators import target_observation_date

MOCK_RAIN_MIN = 0.4
MOCK_RAIN_SPAN = 45.6  # deterministic values in [0.4, 46.0) mm


def _mock_rainfall(cell_id: str, day: date_t) -> float:
    digest = hashlib.sha256(f"{cell_id}|{day.isoformat()}".encode()).digest()
    frac = int.from_bytes(digest[:8], "big") / (2 ** 64)
    return round(MOCK_RAIN_MIN + frac * MOCK_RAIN_SPAN, 2)


class MockObservationSource(ObservationSource):
    """MOCK / TEST ONLY — deterministic fake live observations."""

    name = "mock-sim"
    is_mock = True

    def __init__(self, cells: pd.DataFrame, observation_date: date_t | None = None):
        self.cells = cells[["cell_id", "lat", "lon"]].drop_duplicates().reset_index(drop=True)
        self.observation_date = observation_date

    def fetch(self, now: datetime | None = None) -> SourceResponse:
        now = now or datetime.now(timezone.utc)
        day = self.observation_date or target_observation_date(now, lookback_hours=24.0)
        rows = []
        for _, c in self.cells.iterrows():
            rows.append({
                "cell_id": str(c["cell_id"]),
                "lat": float(c["lat"]),
                "lon": float(c["lon"]),
                "observation_time": datetime(day.year, day.month, day.day,
                                             tzinfo=timezone.utc),
                "rainfall": _mock_rainfall(str(c["cell_id"]), day),
            })
        return SourceResponse(
            source=self.name,
            rows=rows,
            retrieved_at=now,
            metadata={
                "observation_date": day.isoformat(),
                "coverage": f"{len(rows)}/{len(self.cells)} pilot cells",
                "mock": True,
                "warning": "MOCK / TEST ONLY — not operational live data",
            },
        )

    def describe(self) -> dict:
        return {
            "name": self.name,
            "is_mock": True,
            "warning": "MOCK / TEST ONLY — deterministic synthetic observations; "
                       "never use as production live data",
            "units": "mm/day",
        }