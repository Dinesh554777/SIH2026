"""SQLAlchemy 2.0 ORM models for the PostgreSQL application database (Phase I-B).

Tables (aligned to the Phase I-B specification):
- cells           : 304 pilot grid cells, seeded from the authoritative registry
- model_metadata  : frozen model provenance per target (from FREEZE_H.json)
- forecasts       : persisted forecast results (one row per cell+date+version+mode)
- advisories      : decision-support text for a forecast (1 summary + N card rows)

Phase J2 tables (added by migration 0002):
- observations    : normalized live observations (mm/day, timezone-aware)
- ingestion_runs  : provenance/metadata for each ingestion cycle

The scientific Parquet pipeline is not represented here and stays untouched.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (JSON, CheckConstraint, DateTime, ForeignKey, Index,
                        Numeric, String, Text, UniqueConstraint, func)
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship)

from src.ingestion.models import (QUALITY_FUTURE, QUALITY_INVALID,
                                  QUALITY_MISSING, QUALITY_STALE, QUALITY_VALID)


class Base(DeclarativeBase):
    pass


def _prob_check(column: str) -> CheckConstraint:
    return CheckConstraint(
        f"{column} >= 0 AND {column} <= 1", name=f"ck_forecasts_{column}_prob")


class Cell(Base):
    """A pilot grid cell (0.25 deg). Seeded from CellRegistry; NOT a village/block."""

    __tablename__ = "cells"

    id: Mapped[int] = mapped_column(primary_key=True)
    cell_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    latitude: Mapped[float]
    longitude: Mapped[float]
    state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    region: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    forecasts: Mapped[list["Forecast"]] = relationship(back_populates="cell")

    def as_dict(self) -> dict:
        return {
            "cell_id": self.cell_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "region": self.region,
            "state": self.state,
        }


class ModelMetadata(Base):
    """Frozen model provenance, seeded from FREEZE_H.json (one row per target)."""

    __tablename__ = "model_metadata"
    __table_args__ = (
        UniqueConstraint("model_name", "target", "artifact_digest",
                         name="uq_model_metadata_name_target_digest"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    model_name: Mapped[str] = mapped_column(String(32))
    target: Mapped[str] = mapped_column(String(16))
    version: Mapped[str] = mapped_column(String(64))
    feature_group: Mapped[str | None] = mapped_column(String(32), nullable=True)
    training_period: Mapped[str] = mapped_column(String(32))
    validation_period: Mapped[str] = mapped_column(String(32))
    test_period: Mapped[str] = mapped_column(String(32))
    artifact_digest: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    def as_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "target": self.target,
            "version": self.version,
            "feature_group": self.feature_group,
            "artifact_digest": self.artifact_digest,
        }


class Forecast(Base):
    """Persisted forecast for (cell_id, forecast_date, model_version, mode)."""

    __tablename__ = "forecasts"
    __table_args__ = (
        UniqueConstraint("cell_id", "forecast_date", "model_version", "mode",
                         name="uq_forecasts_cell_date_version_mode"),
        _prob_check("onset_probability"),
        _prob_check("break_probability"),
        _prob_check("revival_probability"),
        _prob_check("dry_spell_probability"),
        Index("ix_forecasts_cell_date", "cell_id", "forecast_date"),
        Index("ix_forecasts_date", "forecast_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cell_id: Mapped[str] = mapped_column(ForeignKey("cells.cell_id", ondelete="RESTRICT"))
    forecast_date: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    onset_probability: Mapped[float] = mapped_column(Numeric(6, 4))
    break_probability: Mapped[float] = mapped_column(Numeric(6, 4))
    revival_probability: Mapped[float] = mapped_column(Numeric(6, 4))
    dry_spell_probability: Mapped[float] = mapped_column(Numeric(6, 4))
    model_version: Mapped[str] = mapped_column(String(64))
    mode: Mapped[str] = mapped_column(String(32), default="historical/demo")

    cell: Mapped["Cell"] = relationship(back_populates="forecasts")
    advisories: Mapped[list["Advisory"]] = relationship(
        back_populates="forecast", cascade="all, delete-orphan", passive_deletes=True)


class Advisory(Base):
    """Decision-support text for a forecast (1 summary row + 4 card rows)."""

    __tablename__ = "advisories"
    __table_args__ = (
        UniqueConstraint("forecast_id", "advisory_type", "message",
                         name="uq_advisories_forecast_type_message"),
        CheckConstraint("advisory_type IN ('summary', 'card')", name="ck_advisories_type"),
        Index("ix_advisories_forecast", "forecast_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    forecast_id: Mapped[int] = mapped_column(ForeignKey("forecasts.id", ondelete="CASCADE"))
    advisory_type: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(8), default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    forecast: Mapped["Forecast"] = relationship(back_populates="advisories")


# Phase J2 — live observation persistence -----------------------------------


class Observation(Base):
    """A normalized live rainfall observation (mm/day, timezone-aware).

    Only observations validated as 'valid' by the ingestion layer are stored
    here (rejected rows stay in ingestion_runs.rows_rejected + error_message).
    Missing/invalid rainfall is NEVER silently converted to zero.
    """

    __tablename__ = "observations"
    __table_args__ = (
        UniqueConstraint("cell_id", "observation_time", "source",
                         name="uq_observations_cell_time_source"),
        CheckConstraint("rainfall_mm_day >= 0",
                        name="ck_observations_rainfall_nonnegative"),
        CheckConstraint(
            "quality_flag IN ('valid', 'missing', 'invalid', 'stale', 'future')",
            name="ck_observations_quality_flag"),
        Index("ix_observations_cell_time", "cell_id", "observation_time"),
        Index("ix_observations_time", "observation_time"),
        Index("ix_observations_source", "source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cell_id: Mapped[str] = mapped_column(
        ForeignKey("cells.cell_id", ondelete="RESTRICT"))
    observation_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    latitude: Mapped[float]
    longitude: Mapped[float]
    rainfall_mm_day: Mapped[float]
    source: Mapped[str] = mapped_column(String(32))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    quality_flag: Mapped[str] = mapped_column(String(16), default=QUALITY_VALID)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    cell: Mapped["Cell"] = relationship()

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "cell_id": self.cell_id,
            "observation_time": self.observation_time.isoformat(),
            "latitude": self.latitude,
            "longitude": self.longitude,
            "rainfall_mm_day": self.rainfall_mm_day,
            "source": self.source,
            "retrieved_at": self.retrieved_at.isoformat(),
            "quality_flag": self.quality_flag,
        }


class IngestionRun(Base):
    """Provenance/status record of one ingestion cycle (Phase J2).

    Statuses: RUNNING -> SUCCESS | PARTIAL | FAILED | BLOCKED.
    BLOCKED records a source-connectivity failure (SourceUnavailableError) with
    the real error and ZERO inserted observations — never fabricated data.
    """

    __tablename__ = "ingestion_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED', 'BLOCKED')",
            name="ck_ingestion_runs_status"),
        Index("ix_ingestion_runs_started_at", "started_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="RUNNING")
    rows_received: Mapped[int] = mapped_column(default=0)
    rows_inserted: Mapped[int] = mapped_column(default=0)
    rows_rejected: Mapped[int] = mapped_column(default=0)
    error_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    run_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now())

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "rows_received": self.rows_received,
            "rows_inserted": self.rows_inserted,
            "rows_rejected": self.rows_rejected,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "metadata": self.run_metadata,
        }