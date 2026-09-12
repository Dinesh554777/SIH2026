"""Normalized observation model + ingestion result (Gate J1).

Internal representation shared by every source:

    Observation
    ├─ cell_id          pilot 0.25° grid cell id (deterministic mapping)
    ├─ lat / lon        cell centre (degrees)
    ├─ observation_time timezone-aware timestamp the rainfall refers to (UTC)
    ├─ rainfall_mm      units are EXPLICIT: mm per day
    ├─ source           source identifier (imd, mock, ...)
    ├─ retrieved_at     timezone-aware UTC moment the data reached the system
    ├─ quality_flag     valid | missing | invalid | stale | future
    └─ reason           why the observation is not 'valid' (None when valid)

Quality flags are never silently discarded: rejected observations are returned
with their reason in IngestionResult.rejected.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

QUALITY_VALID = "valid"
QUALITY_MISSING = "missing"
QUALITY_INVALID = "invalid"
QUALITY_STALE = "stale"
QUALITY_FUTURE = "future"

FRESHNESS_FRESH = "fresh"
FRESHNESS_STALE = "stale"
FRESHNESS_FUTURE = "future"
FRESHNESS_UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class Observation:
    cell_id: str
    lat: float
    lon: float
    observation_time: datetime
    rainfall_mm: float
    source: str
    retrieved_at: datetime
    quality_flag: str = QUALITY_VALID
    reason: str | None = None

    def as_dict(self) -> dict:
        return {
            "cell_id": self.cell_id,
            "lat": self.lat,
            "lon": self.lon,
            "observation_time": self.observation_time.isoformat(),
            "rainfall_mm": self.rainfall_mm,
            "source": self.source,
            "retrieved_at": self.retrieved_at.isoformat(),
            "quality_flag": self.quality_flag,
            "reason": self.reason,
        }


@dataclass
class IngestionResult:
    source: str
    status: str  # success | partial | failed
    retrieved_at: datetime | None = None
    observation_time: datetime | None = None  # the latest VALID observation datetime
    rows_received: int = 0
    rows_valid: int = 0
    rows_rejected: int = 0
    freshness: str = FRESHNESS_UNAVAILABLE
    errors: list[str] = field(default_factory=list)
    observations: list[Observation] = field(default_factory=list)
    rejected: list[Observation] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    duration_seconds: float = 0.0

    def as_dict(self) -> dict:
        return {
            "source": self.source,
            "status": self.status,
            "retrieved_at": self.retrieved_at.isoformat() if self.retrieved_at else None,
            "observation_time": (self.observation_time.isoformat()
                                 if self.observation_time else None),
            "rows_received": self.rows_received,
            "rows_valid": self.rows_valid,
            "rows_rejected": self.rows_rejected,
            "freshness": self.freshness,
            "errors": self.errors,
            "metadata": self.metadata,
            "duration_seconds": round(self.duration_seconds, 4),
        }