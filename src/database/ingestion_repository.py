"""Live-ingestion persistence repository (Phase J2).

Writes normalized `observations` and `ingestion_runs` records. No forecasting
logic lives here. Idempotency is enforced by PostgreSQL `ON CONFLICT DO NOTHING`
on the natural key (cell_id, observation_time, source) — repeated ingestion of
an identical observation never duplicates rows, and no destructive
"delete-then-reinsert" behaviour is ever used.

All functions FLUSH but do NOT commit: the caller owns the transaction so an
ingestion cycle (observations + run status) commits atomically.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.database.models import Cell, IngestionRun, Observation
from src.ingestion.models import (QUALITY_FUTURE, QUALITY_INVALID,
                                  QUALITY_MISSING, QUALITY_STALE, QUALITY_VALID,
                                  IngestionResult)

VALID_QUALITIES = {QUALITY_VALID, QUALITY_MISSING, QUALITY_INVALID,
                   QUALITY_STALE, QUALITY_FUTURE}

RUN_RUNNING = "RUNNING"
RUN_SUCCESS = "SUCCESS"
RUN_PARTIAL = "PARTIAL"
RUN_FAILED = "FAILED"
RUN_BLOCKED = "BLOCKED"

_LAT_RANGE = (-90.0, 90.0)
_LON_RANGE = (-180.0, 180.0)


class IngestionPersistenceError(ValueError):
    """Rejected before touching the database (never silently stored)."""


# ---------------------------------------------------------------------- rows
def _validate_observation_row(row: dict, session: Session | None = None) -> dict:
    required = ("cell_id", "observation_time", "latitude", "longitude",
                "source", "retrieved_at")
    missing = [k for k in required if k not in row or row[k] is None]
    if missing:
        raise IngestionPersistenceError(
            f"missing required observation field(s): {','.join(missing)}")

    rain = row.get("rainfall_mm")
    if rain is None:
        raise IngestionPersistenceError(
            "missing rainfall cannot be persisted (never stored as zero)")

    t = row["observation_time"]
    if not isinstance(t, datetime) or t.tzinfo is None:
        raise IngestionPersistenceError(
            "observation_time must be a timezone-aware datetime (UTC)")

    r = row["retrieved_at"]
    if not isinstance(r, datetime) or r.tzinfo is None:
        raise IngestionPersistenceError(
            "retrieved_at must be a timezone-aware datetime (UTC)")

    lat, lon = float(row["latitude"]), float(row["longitude"])
    if not (_LAT_RANGE[0] <= lat <= _LAT_RANGE[1]):
        raise IngestionPersistenceError(f"latitude out of range: {lat}")
    if not (_LON_RANGE[0] <= lon <= _LON_RANGE[1]):
        raise IngestionPersistenceError(f"longitude out of range: {lon}")

    rain = float(rain)
    if not np.isfinite(rain) or rain < 0:
        raise IngestionPersistenceError(
            f"rainfall must be a finite non-negative mm/day value, got {rain!r}")

    quality = str(row.get("quality_flag", QUALITY_VALID))
    if quality not in VALID_QUALITIES:
        raise IngestionPersistenceError(f"unknown quality_flag: {quality!r}")

    if session is not None:
        cell = session.execute(
            select(Cell).where(Cell.cell_id == str(row["cell_id"]))
        ).scalar_one_or_none()
        if cell is None:
            raise IngestionPersistenceError(
                f"unknown cell_id {row['cell_id']!r} (not in the 304-cell registry)")

    return {
        "cell_id": str(row["cell_id"]),
        "observation_time": t.astimezone(timezone.utc),
        "latitude": lat,
        "longitude": lon,
        "rainfall_mm_day": rain,
        "source": str(row["source"]),
        "retrieved_at": r.astimezone(timezone.utc),
        "quality_flag": quality,
    }


def observation_to_row(o) -> dict:
    """Convert a J1 Observation (or ORM Observation) into a repository row dict."""
    return {
        "cell_id": o.cell_id,
        "observation_time": o.observation_time,
        "latitude": float(o.lat if hasattr(o, "lat") else o.latitude),
        "longitude": float(o.lon if hasattr(o, "lon") else o.longitude),
        "rainfall_mm": float(o.rainfall_mm if hasattr(o, "rainfall_mm") else o.rainfall_mm_day),
        "source": o.source,
        "retrieved_at": o.retrieved_at,
        "quality_flag": getattr(o, "quality_flag", QUALITY_VALID),
    }


# ------------------------------------------------------------ observations
def insert_observation(session: Session, *, cell_id: str, observation_time: datetime,
                       latitude: float, longitude: float, rainfall_mm: float,
                       source: str, retrieved_at: datetime,
                       quality_flag: str = QUALITY_VALID) -> Observation | None:
    """Idempotent single insert; returns the row (or None on conflict)."""
    row = _validate_observation_row({
        "cell_id": cell_id, "observation_time": observation_time,
        "latitude": latitude, "longitude": longitude, "rainfall_mm": rainfall_mm,
        "source": source, "retrieved_at": retrieved_at, "quality_flag": quality_flag,
    }, session)
    stmt = (pg_insert(Observation).values(**row)
            .on_conflict_do_nothing(index_elements=["cell_id", "observation_time", "source"])
            .returning(Observation))
    result = session.execute(stmt).scalar_one_or_none()
    session.flush()
    return result


def bulk_insert_observations(session: Session, observations: list) -> int:
    """Idempotent bulk insert; returns the number of rows actually inserted.

    Accepts a list of J1 Observation objects, ORM Observation objects, or dicts.
    Every row is validated first; any invalid row raises IngestionPersistenceError
    (transaction left to the caller to handle).
    """
    if not observations:
        return 0
    rows = [
        _validate_observation_row(
            obs if isinstance(obs, dict) else observation_to_row(obs), session)
        for obs in observations
    ]
    stmt = (pg_insert(Observation).values(rows)
            .on_conflict_do_nothing(index_elements=["cell_id", "observation_time", "source"]))
    result = session.execute(stmt)
    session.flush()
    return int(result.rowcount)


def get_latest_observation(session: Session, cell_id: str) -> Observation | None:
    return session.execute(
        select(Observation)
        .where(Observation.cell_id == cell_id)
        .order_by(Observation.observation_time.desc(), Observation.id.desc())
        .limit(1)
    ).scalar_one_or_none()


def get_observation_history(session: Session, cell_id: str,
                            limit: int = 100) -> list[Observation]:
    return list(session.execute(
        select(Observation)
        .where(Observation.cell_id == cell_id)
        .order_by(Observation.observation_time.desc(), Observation.id.desc())
        .limit(limit)
    ).scalars())


def get_observations_in_range(session: Session, start: datetime, end: datetime,
                              cell_id: str | None = None) -> list[Observation]:
    stmt = select(Observation).where(
        Observation.observation_time >= start,
        Observation.observation_time <= end,
    )
    if cell_id is not None:
        stmt = stmt.where(Observation.cell_id == cell_id)
    stmt = stmt.order_by(Observation.observation_time, Observation.id)
    return list(session.execute(stmt).scalars())


def count_observations(session: Session) -> int:
    return int(session.execute(select(func.count(Observation.id))).scalar_one())


# ------------------------------------------------------------ ingestion runs
def create_ingestion_run(session: Session, *, source: str,
                         started_at: datetime | None = None,
                         status: str = RUN_RUNNING,
                         metadata: dict | None = None) -> IngestionRun:
    if status not in (RUN_RUNNING, RUN_SUCCESS, RUN_PARTIAL, RUN_FAILED, RUN_BLOCKED):
        raise IngestionPersistenceError(f"invalid ingestion run status: {status!r}")
    run = IngestionRun(
        source=source,
        started_at=started_at or datetime.now(timezone.utc),
        status=status,
        rows_received=0,
        rows_inserted=0,
        rows_rejected=0,
        run_metadata=_json_safe(metadata),
    )
    session.add(run)
    session.flush()
    return run


def update_ingestion_run(session: Session, run_id: int, *, status: str | None = None,
                         completed_at: datetime | None = None,
                         rows_received: int | None = None,
                         rows_inserted: int | None = None,
                         rows_rejected: int | None = None,
                         error_type: str | None = None,
                         error_message: str | None = None,
                         metadata: dict | None = None) -> IngestionRun:
    run = session.get(IngestionRun, run_id)
    if run is None:
        raise IngestionPersistenceError(f"ingestion run {run_id} not found")
    if status is not None:
        if status not in (RUN_RUNNING, RUN_SUCCESS, RUN_PARTIAL, RUN_FAILED, RUN_BLOCKED):
            raise IngestionPersistenceError(f"invalid ingestion run status: {status!r}")
        run.status = status
    if completed_at is not None:
        run.completed_at = completed_at
    if rows_received is not None:
        run.rows_received = int(rows_received)
    if rows_inserted is not None:
        run.rows_inserted = int(rows_inserted)
    if rows_rejected is not None:
        run.rows_rejected = int(rows_rejected)
    if error_type is not None:
        run.error_type = error_type
    if error_message is not None:
        run.error_message = error_message
    if metadata is not None:
        run.run_metadata = _json_safe(metadata)
    session.flush()
    return run


def get_ingestion_run(session: Session, run_id: int) -> IngestionRun | None:
    return session.get(IngestionRun, run_id)


def get_latest_ingestion_runs(session: Session, limit: int = 20) -> list[IngestionRun]:
    return list(session.execute(
        select(IngestionRun)
        .order_by(IngestionRun.started_at.desc(), IngestionRun.id.desc())
        .limit(limit)
    ).scalars())


# ------------------------------------------------------------ status mapping
def ingestion_status_for_result(result: IngestionResult) -> tuple[str, str | None]:
    """Map a J1 IngestionResult into an ingestion_runs.status.

    J1 semantics established in the J1 gate:
    - >= one valid observation and no rejections        -> SUCCESS
    - >= one valid observation with some rejections     -> PARTIAL
    - SourceUnavailableError (connectivity)             -> BLOCKED
    - validation / normalization / guard failures       -> FAILED
    """
    if result.status == "success":
        return RUN_SUCCESS, None
    if result.status == "partial":
        return RUN_PARTIAL, None
    err = " ".join(result.errors or [])
    if err.startswith("SourceUnavailableError"):
        return RUN_BLOCKED, "SourceUnavailableError"
    if err.startswith("SourceResponseError"):
        return RUN_FAILED, "SourceResponseError"
    if err.startswith("ValidationError"):
        return RUN_FAILED, "ValidationError"
    if "MOCK" in err:
        return RUN_FAILED, "ConfigurationError"
    if "normalization failed" in err:
        return RUN_FAILED, "ValidationError"
    return RUN_FAILED, "IngestionError"


def _json_safe(value):
    """Coerce dataclass/datetime/numpy values to JSON-serializable primitives."""
    if value is None:
        return None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def json_dumps_safe(value) -> str:
    return json.dumps(_json_safe(value), sort_keys=True, default=str)