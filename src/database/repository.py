"""Application persistence helpers for the PostgreSQL layer (Phase I-B).

Writes APPLICATION records only (cells / forecasts / advisories / model metadata).
The scientific pipeline (Parquet + frozen models) is untouched; callers pass
already-computed probabilities.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from src.database.models import Advisory, Cell, Forecast, ModelMetadata

DEFAULT_MODE = "historical/demo"
FROZEN_VERSION = "FREEZE_H"


def seed_cells(session: Session, cells: pd.DataFrame) -> int:
    """Idempotent seed of pilot cells from the authoritative registry."""
    rows = [
        {
            "cell_id": str(r["cell_id"]),
            "latitude": float(r["lat"]),
            "longitude": float(r["lon"]),
            "state": None,
            "region": str(r["region"]),
        }
        for _, r in cells.iterrows()
    ]
    if not rows:
        return 0
    stmt = pg_insert(Cell).values(rows)
    stmt = stmt.on_conflict_do_nothing(index_elements=["cell_id"])
    session.execute(stmt)
    session.commit()
    return len(rows)


def seed_model_metadata(session: Session, freeze: dict, digest: str) -> int:
    """Idempotent seed of 4 frozen model-provenance rows from FREEZE_H.json."""
    rows = [
        {
            "model_name": spec["selected_model"],
            "target": target,
            "version": FROZEN_VERSION,
            "feature_group": spec.get("feature_group"),
            "training_period": freeze["train_period"],
            "validation_period": freeze["validation_period"],
            "test_period": freeze["test_period"],
            "artifact_digest": digest,
        }
        for target, spec in freeze["targets"].items()
    ]
    stmt = pg_insert(ModelMetadata).values(rows)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["model_name", "target", "artifact_digest"])
    session.execute(stmt)
    session.commit()
    return len(rows)


def upsert_forecast(session: Session, *, cell_id: str, forecast_date,
                    onset_probability: float, break_probability: float,
                    revival_probability: float, dry_spell_probability: float,
                    model_version: str = FROZEN_VERSION, mode: str = DEFAULT_MODE,
                    generated_at: datetime | None = None) -> int:
    """Idempotent insert of a forecast row; returns the forecast id."""
    as_date = pd.Timestamp(forecast_date).date()
    stmt = pg_insert(Forecast).values(
        cell_id=cell_id,
        forecast_date=as_date,
        generated_at=generated_at or datetime.now(timezone.utc),
        onset_probability=float(onset_probability),
        break_probability=float(break_probability),
        revival_probability=float(revival_probability),
        dry_spell_probability=float(dry_spell_probability),
        model_version=model_version,
        mode=mode,
    )
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["cell_id", "forecast_date", "model_version", "mode"])
    stmt = stmt.returning(Forecast.id)
    row_id = session.execute(stmt).scalar_one_or_none()
    session.flush()
    if row_id is not None:
        return int(row_id)
    # idempotent conflict -> re-select the existing row
    return int(session.execute(
        select(Forecast.id).where(
            Forecast.cell_id == cell_id,
            Forecast.forecast_date == as_date,
            Forecast.model_version == model_version,
            Forecast.mode == mode,
        )
    ).scalar_one())


def _advisory_messages(bundle: dict) -> list[tuple[str, str]]:
    """Return (advisory_type, message) rows for a rules bundle: 1 summary + 4 cards."""
    cards = bundle["cards"]
    dominant = bundle.get("dominant") or max(cards, key=lambda c: c["probability"])["state"]
    summary = bundle.get("summary") or (
        f"{next(c['state_label'] for c in cards if c['state'] == dominant)} probability is "
        f"{next(c['probability_pct'] for c in cards if c['state'] == dominant):.0f}% "
        f"({next(c['band'] for c in cards if c['state'] == dominant)}). "
        f"{next(c['interpretation'] for c in cards if c['state'] == dominant)}")
    rows = [("summary", summary)]
    for c in cards:
        rows.append(("card", f"{c['interpretation']} {c['suggested_action']}"))
    return rows


def insert_advisories(session: Session, forecast_id: int, bundle: dict) -> int:
    """Persist the deterministic advisory bundle: 1 summary row + 4 card rows."""
    rows = [{"forecast_id": forecast_id, "advisory_type": t, "message": m, "language": "en"}
            for t, m in _advisory_messages(bundle)]
    stmt = pg_insert(Advisory).values(rows)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["forecast_id", "advisory_type", "message"])
    session.execute(stmt)
    session.commit()
    return len(rows)


def store_forecast_bundle(session: Session, *, cell_id: str, forecast_date,
                          probabilities: dict, model_version: str = FROZEN_VERSION,
                          mode: str = DEFAULT_MODE, bundle: dict,
                          generated_at: datetime | None = None) -> int:
    """Persist a full forecast + advisory bundle in one transaction; returns forecast id."""
    fid = upsert_forecast(
        session,
        cell_id=cell_id,
        forecast_date=forecast_date,
        onset_probability=probabilities["onset"],
        break_probability=probabilities["break"],
        revival_probability=probabilities["revival"],
        dry_spell_probability=probabilities["dry_spell"],
        model_version=model_version,
        mode=mode,
        generated_at=generated_at,
    )
    insert_advisories(session, fid, bundle)
    return fid


def get_forecasts_for_cell(session: Session, cell_id: str,
                           limit: int = 30) -> list[Forecast]:
    rows = session.execute(
        select(Forecast)
        .where(Forecast.cell_id == cell_id)
        .order_by(Forecast.forecast_date.desc())
        .limit(limit)
    ).scalars().all()
    return list(rows)


def get_advisories(session: Session, forecast_id: int) -> list[Advisory]:
    rows = session.execute(
        select(Advisory)
        .where(Advisory.forecast_id == forecast_id)
        .order_by(Advisory.advisory_type, Advisory.id)
    ).scalars().all()
    return list(rows)


def get_cell(session: Session, cell_id: str) -> Cell | None:
    return session.execute(
        select(Cell).where(Cell.cell_id == cell_id)
    ).scalar_one_or_none()


def count_rows(session: Session, model) -> int:
    return int(session.execute(select(func.count(model.id))).scalar_one())


def table_names(session: Session, schema: str = "public") -> list[str]:
    rows = session.execute(
        text("SELECT tablename FROM pg_tables WHERE schemaname = :s ORDER BY tablename"),
        {"s": schema},
    ).all()
    return [r[0] for r in rows]