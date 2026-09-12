"""Per-observation validators (Gate J1).

Validation is deterministic and never mutates values: impossible rainfall is
REJECTED (never coerced to zero), timestamps are classified (fresh/stale/future)
against the actual observation time, coordinates are range-checked, and any
missing required field is recorded with an explicit reason.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np

from src.ingestion.models import (QUALITY_FUTURE, QUALITY_INVALID,
                                  QUALITY_MISSING, QUALITY_STALE, QUALITY_VALID)

REQUIRED_ROW_KEYS = ("lat", "lon", "observation_time")

LAT_MIN, LAT_MAX = -90.0, 90.0
LON_MIN, LON_MAX = -180.0, 180.0


def _is_number(v) -> bool:
    try:
        float(v)
    except (TypeError, ValueError):
        return False
    return True


def check_required_fields(row: dict) -> tuple[bool, str | None]:
    """Presence checks for lat/lon/observation_time.

    rainfall is a SEPARATE concern: a present-but-None rainfall means 'missing
    measurement' (quality=missing), never a schema failure.
    """
    missing = [k for k in REQUIRED_ROW_KEYS if k not in row or row[k] is None]
    if missing:
        return False, f"missing required field(s): {','.join(missing)}"
    return True, None


def check_coordinates(lat, lon) -> tuple[bool, str | None]:
    if not _is_number(lat) or not _is_number(lon):
        return False, f"non-numeric coordinates (lat={lat!r}, lon={lon!r})"
    if not (LAT_MIN <= float(lat) <= LAT_MAX):
        return False, f"latitude out of range [-90, 90]: {lat!r}"
    if not (LON_MIN <= float(lon) <= LON_MAX):
        return False, f"longitude out of range [-180, 180]: {lon!r}"
    return True, None


def check_rainfall(value) -> tuple[bool, str | None]:
    if value is None:
        return False, "rainfall missing"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False, f"rainfall not numeric: {value!r}"
    if not np.isfinite(v):
        return False, f"rainfall not finite: {value!r}"
    if v < 0.0:
        return False, f"negative rainfall rejected (mm/day units): {v}"
    return True, None


def check_timestamp(value, now: datetime,
                    max_age_hours: float, future_tolerance_seconds: float
                    ) -> tuple[str, str | None]:
    """Classify an observation timestamp.

    Returns (quality_flag, reason). quality_flag is one of
    valid / stale / future / invalid.

    - future:  observation_time > now + future_tolerance
    - stale:   now - observation_time > max_age_hours
    - valid:   fresh (within max_age_hours)
    - invalid: not a timestamp, or missing tzinfo
    """
    if not isinstance(value, datetime):
        return QUALITY_INVALID, f"observation_time not a datetime: {value!r}"
    dt = value
    if dt.tzinfo is None:
        return QUALITY_INVALID, "observation_time must be timezone-aware (UTC)"
    dt = dt.astimezone(timezone.utc)
    age = now.astimezone(timezone.utc) - dt
    if age.total_seconds() < -future_tolerance_seconds:
        return QUALITY_FUTURE, f"observation_time in the future by {-age.total_seconds():.0f}s"
    if age.total_seconds() > max_age_hours * 3600.0:
        return QUALITY_STALE, f"observation older than {max_age_hours:.0f}h (age {age.days}d+"
    return QUALITY_VALID, None


def classify_freshness(observation_time: datetime | None, now: datetime,
                       max_age_hours: float, future_tolerance_seconds: float) -> str:
    """Batch-level freshness over the latest successfully-dated observation.

    Returns one of fresh | stale | future | unavailable.
    """
    if observation_time is None:
        return "unavailable"
    flag = check_timestamp(observation_time, now, max_age_hours,
                           future_tolerance_seconds)[0]
    if flag == QUALITY_VALID:
        return "fresh"
    if flag == QUALITY_INVALID:
        return "unavailable"
    return flag


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return value.astimezone(timezone.utc)


def target_observation_date(now: datetime, lookback_hours: float = 24.0) -> "date":
    """The daily-observation day the source should provide: the last COMPLETED day."""
    from datetime import date

    return date.fromtimestamp(
        (now.astimezone(timezone.utc) - timedelta(hours=lookback_hours)).timestamp())