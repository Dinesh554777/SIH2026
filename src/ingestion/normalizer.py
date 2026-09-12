"""Normalization: source response -> normalized Observation objects (Gate J1).

Pipeline per raw row:

    lat/lon -> deterministic pilot-cell mapping (CellMapper)
    every required field validated
    rainfall checked (units: mm/day; never coerced)
    timestamp parsed + classified (fresh/stale/future/invalid)
    -> Observation (valid)  or  rejected Observation (with quality + reason)

Rejected rows are returned (never silently dropped): quality_flag + reason record
the outcome so J2 persistence and operators can audit what was refused.
"""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.ingestion.models import (Observation, QUALITY_INVALID, QUALITY_MISSING,
                                  QUALITY_VALID)
from src.ingestion.validators import (check_coordinates, check_rainfall,
                                      check_required_fields, check_timestamp)

# Half a 0.25° grid step + numeric tolerance for cell mapping.
CELL_TOLERANCE_DEG = 0.125 + 1e-6


def _parse_dt(value, now: datetime) -> tuple[datetime | None, str | None]:
    if isinstance(value, datetime):
        return value, None
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")), None
        except ValueError:
            return None, f"unparseable timestamp {value!r}"
    return None, f"timestamp not a datetime/ISO string: {value!r}"


class CellMapper:
    """Deterministic (lat, lon) -> pilot 0.25° cell_id mapping.

    Uses nearest-cell lookup over the registered pilot cells; a coordinate within
    half a grid step (0.125° + tolerance) of a cell centre maps to that cell.
    Ties resolve deterministically to the lexicographically-first cell centre
    because the registry is sorted by (lat, lon). No administrative boundary
    semantics are implied.
    """

    def __init__(self, cells: pd.DataFrame):
        if not {"cell_id", "lat", "lon"}.issubset(cells.columns):
            raise ValueError("cells must contain cell_id, lat, lon")
        df = cells[["cell_id", "lat", "lon"]].drop_duplicates()
        df = df.sort_values(["lat", "lon"]).reset_index(drop=True)
        self.cells = df
        self._lat = df["lat"].to_numpy(dtype=float)
        self._lon = df["lon"].to_numpy(dtype=float)

    def resolve(self, lat: float, lon: float) -> tuple[str | None, str | None]:
        """Return (cell_id, reason). reason is None on success."""
        dlat = self._lat - float(lat)
        dlon = self._lon - float(lon)
        dist2 = dlat * dlat + dlon * dlon
        i = int(np.argmin(dist2))
        if np.sqrt(dist2[i]) <= CELL_TOLERANCE_DEG:
            return str(self.cells["cell_id"].iloc[i]), None
        return None, (f"coordinate ({lat}, {lon}) not within a pilot cell "
                      f"(nearest {self.cells['cell_id'].iloc[i]} "
                      f"at {dist2[i] ** 0.5:.4f} deg)")

    def resolve_all(self, rows_meta: list[tuple[float, float]]) -> list[tuple[str | None, str | None]]:
        return [self.resolve(lat, lon) for lat, lon in rows_meta]

    @classmethod
    def from_matrix(cls, matrix: pd.DataFrame) -> "CellMapper":
        from src.serving.registry import load_cells

        return cls(load_cells(matrix))


def normalize_batch(rows: list[dict], source: str, retrieved_at: datetime,
                    mapper: CellMapper, now: datetime,
                    max_age_hours: float, future_tolerance_seconds: float,
                    ) -> tuple[list[Observation], list[Observation], list[datetime]]:
    """Normalize raw source rows -> (valid, rejected, parsed_observation_times).

    parsed_observation_times is the set of every successfully-parsed, tz-aware
    observation time in the batch (valid AND rejected alike), used for honest
    batch-level freshness classification (e.g. an all-stale batch must read
    'stale', not 'available').
    """
    if retrieved_at.tzinfo is None:
        raise ValueError("retrieved_at must be timezone-aware")
    valid: list[Observation] = []
    rejected: list[Observation] = []
    parsed_times: list[datetime] = []
    for row in rows:
        ok, reason = check_required_fields(row)
        if not ok:
            rejected.append(_refuse(row, source, retrieved_at, QUALITY_INVALID, reason))
            continue

        ok, reason = check_coordinates(row["lat"], row["lon"])
        if not ok:
            rejected.append(_refuse(row, source, retrieved_at, QUALITY_INVALID, reason))
            continue

        cell_id, reason = mapper.resolve(float(row["lat"]), float(row["lon"]))
        if reason is not None:
            rejected.append(_refuse(row, source, retrieved_at, QUALITY_INVALID, reason))
            continue

        dt, reason = _parse_dt(row["observation_time"], now)
        if reason is not None:
            rejected.append(_refuse(row, source, retrieved_at, QUALITY_INVALID, reason))
            continue
        if dt.tzinfo is not None:
            parsed_times.append(dt.astimezone(timezone.utc))
        flag, reason = check_timestamp(dt, now, max_age_hours, future_tolerance_seconds)
        if flag != QUALITY_VALID:
            rejected.append(_refuse(row, source, retrieved_at, flag, reason))
            continue

        if row["rainfall"] is None:
            rejected.append(_refuse(row, source, retrieved_at, QUALITY_MISSING,
                                    "rainfall missing"))
            continue
        ok, reason = check_rainfall(row["rainfall"])
        if not ok:
            rejected.append(_refuse(row, source, retrieved_at, QUALITY_INVALID, reason))
            continue

        valid.append(Observation(
            cell_id=cell_id,
            lat=float(row["lat"]),
            lon=float(row["lon"]),
            observation_time=dt.astimezone(timezone.utc),
            rainfall_mm=float(row["rainfall"]),
            source=source,
            retrieved_at=retrieved_at.astimezone(timezone.utc),
            quality_flag=QUALITY_VALID,
            reason=None,
        ))
    return valid, rejected, parsed_times


def _refuse(row: dict, source: str, retrieved_at: datetime, flag: str,
            reason: str | None) -> Observation:
    return Observation(
        cell_id=str(row.get("cell_id") or ""),
        lat=_safe_float(row.get("lat")),
        lon=_safe_float(row.get("lon")),
        observation_time=_safe_dt(row.get("observation_time")),
        rainfall_mm=_safe_float(row.get("rainfall")),
        source=source,
        retrieved_at=retrieved_at.astimezone(timezone.utc),
        quality_flag=flag,
        reason=reason,
    )


def _safe_float(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def _safe_dt(v) -> datetime:
    if isinstance(v, datetime) and v.tzinfo is not None:
        return v
    if isinstance(v, str):
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(timezone.utc)