"""Phase J2 — OFFLINE schema/validation tests (no PostgreSQL required).

These tests always run. They introspect the SQLAlchemy model metadata (via a
throwaway SQLite database) to prove the observations/ingestion_runs schema
definitions, constraints and indexes, exercise repository pre-validation rules,
and cover ingestion-run status mapping — none of which need a real database.

Live PostgreSQL behavior (idempotent ON CONFLICT inserts, real migrations,
pipeline integration) lives in tests/test_phase_j2_db.py.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.ingestion_repository import (  # noqa: E402
    IngestionPersistenceError, RUN_BLOCKED, RUN_FAILED, RUN_PARTIAL,
    RUN_SUCCESS, _validate_observation_row, create_ingestion_run,
    get_ingestion_run, ingestion_status_for_result, update_ingestion_run)
from src.database.models import (Base, Cell, IngestionRun, Observation)  # noqa: E402
from src.ingestion.models import IngestionResult, QUALITY_VALID  # noqa: E402

from sqlalchemy import CheckConstraint, UniqueConstraint  # noqa: E402

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)

OBSERVATION_COLUMNS = {
    "id", "cell_id", "observation_time", "latitude", "longitude",
    "rainfall_mm_day", "source", "retrieved_at", "quality_flag", "created_at",
}
RUN_COLUMNS = {
    "id", "source", "started_at", "completed_at", "status",
    "rows_received", "rows_inserted", "rows_rejected",
    "error_type", "error_message", "metadata", "created_at",
}


@pytest.fixture(scope="module")
def sqlite_engine():
    eng = create_engine("sqlite://")
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture(scope="module")
def inspector(sqlite_engine):
    return inspect(sqlite_engine)


@pytest.fixture()
def session(sqlite_engine):
    from sqlalchemy.orm import Session

    with Session(sqlite_engine) as s:
        yield s
        s.rollback()


# ------------------------------------------------------------------- schema
class TestSchemaDefinitions:
    def test_tables_exist(self, inspector):
        names = set(inspector.get_table_names())
        assert {"observations", "ingestion_runs"} <= names
        assert {"cells", "forecasts", "advisories", "model_metadata"} <= names

    def test_observations_columns(self, inspector):
        cols = {c["name"] for c in inspector.get_columns("observations")}
        assert cols == OBSERVATION_COLUMNS

    def test_observations_unique_constraint(self, inspector):
        uniques = inspector.get_unique_constraints("observations")
        by_name = {u["name"]: u for u in uniques}
        assert "uq_observations_cell_time_source" in by_name
        assert set(by_name["uq_observations_cell_time_source"]["column_names"]) == {
            "cell_id", "observation_time", "source"}

    def test_observations_check_constraints(self, inspector):
        # SQLite reflection does not surface CHECK bodies; introspect the model
        # metadata (offline definitions) instead.
        checks = [c for c in Base.metadata.tables["observations"].constraints
                  if isinstance(c, CheckConstraint)]
        text_sql = "\n".join(str(c.sqltext) for c in checks)
        assert "rainfall_mm_day >= 0" in text_sql
        assert "quality_flag IN" in text_sql

    def test_observations_indexes(self, inspector):
        idx = {i["name"] for i in inspector.get_indexes("observations")}
        assert {"ix_observations_cell_time", "ix_observations_time",
                "ix_observations_source"} <= idx
        cell_time = next(i for i in inspector.get_indexes("observations")
                         if i["name"] == "ix_observations_cell_time")
        assert set(cell_time["column_names"]) == {"cell_id", "observation_time"}

    def test_observations_fk_to_cells(self, inspector):
        fks = inspector.get_foreign_keys("observations")
        assert any(
            fk["referred_table"] == "cells"
            and set(fk["constrained_columns"]) == {"cell_id"}
            for fk in fks)

    def test_ingestion_runs_schema(self, inspector):
        cols = {c["name"] for c in inspector.get_columns("ingestion_runs")}
        assert cols == RUN_COLUMNS
        checks = [c2 for c2 in Base.metadata.tables["ingestion_runs"].constraints
                  if isinstance(c2, CheckConstraint)]
        assert any("status IN" in str(c2.sqltext) for c2 in checks)
        idx = {i["name"] for i in inspector.get_indexes("ingestion_runs")}
        assert "ix_ingestion_runs_started_at" in idx

    def test_quality_flag_unique_name_exists(self):
        uqs = [u for u in Base.metadata.tables["observations"].constraints
               if isinstance(u, UniqueConstraint)]
        assert any(u.name == "uq_observations_cell_time_source"
                   and set(u.columns.keys()) == {"cell_id", "observation_time", "source"}
                   for u in uqs)


# ------------------------------------------------------------ repository validation
class TestRepositoryValidation:
    def _cell(self, session):
        session.add(Cell(cell_id="10.00_76.25", latitude=10.0, longitude=76.25,
                         region="TN"))
        session.flush()

    def _row(self, **over):
        base = {"cell_id": "10.00_76.25", "observation_time": NOW,
                "latitude": 10.0, "longitude": 76.25, "rainfall_mm": 5.0,
                "source": "imd", "retrieved_at": NOW}
        base.update(over)
        return base

    def test_valid_row(self, session):
        self._cell(session)
        row = _validate_observation_row(self._row(), session)
        assert row["rainfall_mm_day"] == 5.0
        assert row["quality_flag"] == QUALITY_VALID
        assert row["observation_time"].tzinfo is not None

    def test_negative_rainfall_rejected(self, session):
        self._cell(session)
        with pytest.raises(IngestionPersistenceError, match="non-negative"):
            _validate_observation_row(self._row(rainfall_mm=-1.0), session)

    def test_nan_rainfall_rejected(self, session):
        self._cell(session)
        with pytest.raises(IngestionPersistenceError, match="finite"):
            _validate_observation_row(self._row(rainfall_mm=float("nan")), session)

    def test_none_rainfall_rejected_not_zero(self, session):
        self._cell(session)
        with pytest.raises(IngestionPersistenceError, match="never stored as zero"):
            _validate_observation_row(self._row(rainfall_mm=None), session)

    def test_naive_timestamp_rejected(self, session):
        self._cell(session)
        with pytest.raises(IngestionPersistenceError, match="timezone-aware"):
            _validate_observation_row(
                self._row(observation_time=datetime(2026, 9, 12, 6, 0)), session)

    def test_missing_fields_rejected(self, session):
        self._cell(session)
        with pytest.raises(IngestionPersistenceError, match="missing required"):
            _validate_observation_row({"cell_id": "10.00_76.25"}, session)

    def test_unknown_cell_rejected(self, session):
        with pytest.raises(IngestionPersistenceError, match="unknown cell_id"):
            _validate_observation_row(self._row(cell_id="99.99_99.99"), session)


# ------------------------------------------------------------ constraint offline
class TestConstraintOffline:
    def test_unique_constraint_blocks_duplicate(self, session):
        session.add(Cell(cell_id="10.00_76.25", latitude=10.0, longitude=76.25, region="TN"))
        session.flush()
        o = {
            "cell_id": "10.00_76.25", "observation_time": NOW,
            "latitude": 10.0, "longitude": 76.25, "rainfall_mm_day": 3.0,
            "source": "imd", "retrieved_at": NOW, "quality_flag": QUALITY_VALID,
        }
        session.add(Observation(**o))
        session.commit()
        session.add(Observation(**o))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        n = session.execute(
            text("SELECT COUNT(*) FROM observations")).scalar_one()
        assert n == 1


# ------------------------------------------------------------ run status mapping
class TestRunStatusMapping:
    def _result(self, status="success", errors=None):
        return IngestionResult(source="imd", status=status, errors=errors or [])

    def test_success(self):
        assert ingestion_status_for_result(self._result()) == (RUN_SUCCESS, None)

    def test_partial(self):
        assert ingestion_status_for_result(
            self._result("partial")) == (RUN_PARTIAL, None)

    def test_blocked_on_source_unavailable(self):
        assert ingestion_status_for_result(self._result(
            "failed", ["SourceUnavailableError: connection refused"])
        ) == (RUN_BLOCKED, "SourceUnavailableError")

    def test_failed_on_malformed_response(self):
        assert ingestion_status_for_result(self._result(
            "failed", ["SourceResponseError: bad payload"])
        ) == (RUN_FAILED, "SourceResponseError")

    def test_failed_on_validation(self):
        assert ingestion_status_for_result(self._result(
            "failed", ["normalization failed: boom"])) == (RUN_FAILED, "ValidationError")


# ------------------------------------------------------------ run lifecycle offline
class TestRunLifecycleOffline:
    def test_create_then_update(self, session):
        start = NOW - timedelta(minutes=1)
        run = create_ingestion_run(session, source="imd", started_at=start)
        assert run.status == "RUNNING"
        session.commit()
        rid = int(run.id)

        update_ingestion_run(session, rid, status="SUCCESS", completed_at=NOW,
                             rows_received=304, rows_inserted=304, rows_rejected=0)
        session.commit()

        got = get_ingestion_run(session, rid)
        assert got.status == "SUCCESS"
        assert got.rows_received == 304 and got.rows_inserted == 304
        assert got.completed_at is not None  # sqlite drops tz; PG verified in the live module

    def test_statuses_constrained(self, session):
        run = create_ingestion_run(session, source="imd", started_at=NOW)
        session.commit()
        with pytest.raises(IngestionPersistenceError):
            update_ingestion_run(session, run.id, status="WAT")
        # the "metadata" JSON column round-trips dicts on sqlite
        update_ingestion_run(session, run.id, status="BLOCKED",
                             error_type="SourceUnavailableError",
                             error_message="connection refused",
                             metadata={"source_is_mock": False, "n": 1})
        session.commit()
        got = get_ingestion_run(session, run.id)
        assert got.status == "BLOCKED"
        assert got.error_type == "SourceUnavailableError"
        assert got.run_metadata == {"source_is_mock": False, "n": 1}