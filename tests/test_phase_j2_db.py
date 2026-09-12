"""Phase J2 — live PostgreSQL integration tests.

The whole module is skipped when the PostgreSQL test DSN is not configured or
unreachable (same convention as tests/test_database.py), so CI without a DB
still passes. When a DB is available, this module exercises the REAL migration
path (empty DB -> alembic upgrade head, twice) and the idempotent
PostgreSQL ON CONFLICT inserts, plus the J1 pipeline (BLOCKED on unreachable
source, MOCK/TEST-ONLY path behind allow_mock).
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database.config import test_database_url as _test_dsn  # noqa: E402
from src.database.db import _engine_for, ping_test  # noqa: E402
from src.database.ingestion_repository import (  # noqa: E402
    RUN_BLOCKED, RUN_FAILED, RUN_SUCCESS, bulk_insert_observations,
    count_observations, create_ingestion_run, get_ingestion_run,
    get_latest_ingestion_runs, get_latest_observation,
    get_observation_history, get_observations_in_range, insert_observation,
    update_ingestion_run)
from src.database.models import (Base, Cell, Observation)  # noqa: E402
from src.ingestion.clients.base import ObservationSource, SourceResponse  # noqa: E402
from src.ingestion.clients.mock import MockObservationSource  # noqa: E402
from src.ingestion.errors import SourceUnavailableError  # noqa: E402
from src.ingestion.normalizer import CellMapper  # noqa: E402
from src.ingestion.pipeline import IngestionPipeline  # noqa: E402
from src.ingestion.validators import QUALITY_VALID  # noqa: E402

pytestmark = pytest.mark.skipif(
    not (_test_dsn() and ping_test()),
    reason="PostgreSQL test database unavailable (see .env.example / scripts/setup_pg_db.sql)")

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)

_LATS = [10.0, 10.25]
_LONS = [76.25, 76.5]


def build_cells() -> pd.DataFrame:
    rows = []
    for lat in _LATS:
        for lon in _LONS:
            rows.append({"cell_id": f"{lat:.2f}_{lon:.2f}", "lat": lat, "lon": lon})
    return pd.DataFrame(rows)


@pytest.fixture(scope="module")
def engine():
    url = _test_dsn()
    eng = _engine_for(url)

    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    os.environ["DATABASE_URL"] = url
    try:
        with eng.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()
        command.upgrade(cfg, "head")

        with eng.connect() as conn:  # freshly empty -> empty-init reproducibility
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()
        command.upgrade(cfg, "head")
    finally:
        os.environ.pop("DATABASE_URL", None)

    yield eng

    Base.metadata.drop_all(eng)
    with eng.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
    eng.dispose()


@pytest.fixture(scope="module")
def session_factory(engine):
    from src.database.db import session_factory as _sf

    return _sf(engine)


@pytest.fixture(autouse=True)
def clean_tables(session_factory):
    yield
    with session_factory() as s:
        s.execute(text("TRUNCATE observations, ingestion_runs, cells "
                       "RESTART IDENTITY CASCADE"))
        s.commit()


@pytest.fixture()
def cells() -> pd.DataFrame:
    return build_cells()


@pytest.fixture()
def seeded_cells(session_factory, cells):
    with session_factory() as s:
        for _, r in cells.iterrows():
            s.add(Cell(cell_id=str(r["cell_id"]), latitude=float(r["lat"]),
                       longitude=float(r["lon"]), region="TN"))
        s.commit()
    return cells


def _obs(cell_id="10.00_76.25", t=None, source="imd", rain=5.0):
    return {"cell_id": cell_id, "observation_time": t or (NOW - timedelta(hours=1)),
            "latitude": 10.0, "longitude": 76.25, "rainfall_mm": rain,
            "source": source, "retrieved_at": NOW, "quality_flag": QUALITY_VALID}


# --------------------------------------------------------------- schema live
class TestSchemaLive:
    def test_tables_and_columns(self, session_factory):
        with session_factory() as s:
            for table, cols in [
                ("observations", {"id", "cell_id", "observation_time", "latitude",
                                  "longitude", "rainfall_mm_day", "source",
                                  "retrieved_at", "quality_flag", "created_at"}),
                ("ingestion_runs", {"id", "source", "started_at", "completed_at",
                                    "status", "rows_received", "rows_inserted",
                                    "rows_rejected", "error_type", "error_message",
                                    "metadata", "created_at"}),
            ]:
                present = set(s.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = :t"), {"t": table}).scalars())
                assert cols <= present, table

    def test_observation_time_is_timestamptz(self, session_factory):
        with session_factory() as s:
            data_types = set(s.execute(text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name='observations' AND column_name IN "
                "('observation_time', 'retrieved_at')")).scalars())
        assert data_types == {"timestamp with time zone"}

    def test_unique_constraint_and_indexes(self, session_factory):
        with session_factory() as s:
            uq = set(s.execute(text(
                "SELECT conname FROM pg_constraint WHERE conrelid='observations'::regclass "
                "AND contype='u'")).scalars())
            assert "uq_observations_cell_time_source" in uq
            idx = set(s.execute(text(
                "SELECT indexname FROM pg_indexes WHERE tablename='observations'")).scalars())
            assert {"ix_observations_cell_time", "ix_observations_time",
                    "ix_observations_source"} <= idx


# ------------------------------------------------------------ persistence
class TestObservationPersistence:
    def test_single_insert_and_retrieve(self, session_factory, seeded_cells):
        with session_factory() as s:
            row = insert_observation(s, **_obs())
            s.commit()
            oid = row.id
            assert row.rainfall_mm_day == 5.0
            got = s.get(Observation, oid)
            assert got.cell_id == "10.00_76.25"
            assert got.observation_time.tzinfo is not None
            assert got.retrieved_at.tzinfo is not None
            assert got.source == "imd"

    def test_bulk_insert(self, session_factory, seeded_cells):
        obs = [_obs(cell_id=f"{lat:.2f}_{lon:.2f}", t=NOW)
               for lat in _LATS for lon in _LONS]
        with session_factory() as s:
            n = bulk_insert_observations(s, obs)
            s.commit()
            assert n == 4
            assert count_observations(s) == 4

    def test_retrieve_by_cell(self, session_factory, seeded_cells):
        with session_factory() as s:
            bulk_insert_observations(s, [
                _obs(cell_id="10.00_76.25", t=NOW - timedelta(days=2)),
                _obs(cell_id="10.00_76.25", t=NOW),
                _obs(cell_id="10.25_76.50", t=NOW),
            ]); s.commit()
        with session_factory() as s:
            hist = get_observation_history(s, "10.00_76.25")
            assert [h.observation_time for h in hist] == sorted(
                [h.observation_time for h in hist], reverse=True)
            assert len(hist) == 2
            latest = get_latest_observation(s, "10.00_76.25")
            assert latest.observation_time == NOW

    def test_retrieve_by_time_range(self, session_factory, seeded_cells):
        start = NOW - timedelta(days=5)
        with session_factory() as s:
            bulk_insert_observations(s, [
                _obs(t=start),
                _obs(cell_id="10.25_76.50", t=NOW),
                _obs(cell_id="10.00_76.25", t=NOW - timedelta(days=50)),
            ]); s.commit()
        with session_factory() as s:
            rows = get_observations_in_range(s, start, NOW)
            assert len(rows) == 2
            rows_cell = get_observations_in_range(s, start, NOW, cell_id="10.25_76.50")
            assert len(rows_cell) == 1

    def test_idempotent_single_insert(self, session_factory, seeded_cells):
        with session_factory() as s:
            first = insert_observation(s, **_obs())
            s.commit()
            second = insert_observation(s, **_obs())
            s.commit()
            assert first is not None
            assert second is None  # conflict -> no duplicate
            assert count_observations(s) == 1

    def test_idempotent_bulk_insert(self, session_factory, seeded_cells):
        with session_factory() as s:
            n1 = bulk_insert_observations(s, [_obs() for _ in range(3)])
            s.commit()
            n2 = bulk_insert_observations(s, [_obs() for _ in range(3)])
            s.commit()
            assert n1 == 1 and n2 == 0  # second identical batch inserts nothing
            assert count_observations(s) == 1


# ------------------------------------------------------------ validation live
class TestPersistenceValidation:
    def test_negative_rainfall_rejected(self, session_factory, seeded_cells):
        from src.database.ingestion_repository import IngestionPersistenceError
        with session_factory() as s:
            with pytest.raises(IngestionPersistenceError):
                insert_observation(s, **_obs(rain=-2.0))
            s.rollback()
            assert count_observations(s) == 0

    def test_unknown_cell_rejected(self, session_factory):
        from src.database.ingestion_repository import IngestionPersistenceError
        with session_factory() as s:
            with pytest.raises(IngestionPersistenceError, match="unknown cell_id"):
                insert_observation(s, **_obs(cell_id="99.99_99.99"))
            s.rollback()

    def test_naive_timestamp_rejected(self, session_factory, seeded_cells):
        from src.database.ingestion_repository import IngestionPersistenceError
        with session_factory() as s:
            with pytest.raises(IngestionPersistenceError, match="timezone-aware"):
                insert_observation(s, **_obs(
                    t=datetime(2026, 9, 12, 6, 0)))  # naive
            s.rollback()

    def test_db_check_constraint_blocks_negative(self, session_factory, seeded_cells):
        import sqlalchemy
        from sqlalchemy.exc import IntegrityError
        with session_factory() as s:
            stmt = sqlalchemy.dialects.postgresql.insert(Observation).values(
                cell_id="10.00_76.25", observation_time=NOW, latitude=10.0,
                longitude=76.25, rainfall_mm_day=-5.0, source="imd",
                retrieved_at=NOW, quality_flag=QUALITY_VALID)
            with pytest.raises(IntegrityError):
                s.execute(stmt); s.commit()
            s.rollback()


# ------------------------------------------------------------ ingestion runs live
class TestIngestionRunsLive:
    def test_running_to_success_preserves_counts(self, session_factory):
        with session_factory() as s:
            run = create_ingestion_run(s, source="imd", started_at=NOW - timedelta(seconds=5))
            s.commit()
            rid = int(run.id)
            update_ingestion_run(s, rid, status="SUCCESS", completed_at=NOW,
                                 rows_received=304, rows_inserted=304, rows_rejected=0)
            s.commit()
            got = get_ingestion_run(s, rid)
            assert got.status == "SUCCESS"
            assert (got.rows_received, got.rows_inserted, got.rows_rejected) == (304, 304, 0)

    def test_running_to_failed_preserves_error(self, session_factory):
        with session_factory() as s:
            run = create_ingestion_run(s, source="imd", started_at=NOW)
            s.commit()
            update_ingestion_run(s, run.id, status="FAILED", completed_at=NOW,
                                 error_type="ValidationError",
                                 error_message="rainfall not finite: nan")
            s.commit()
            got = get_ingestion_run(s, run.id)
            assert got.status == "FAILED"
            assert got.error_type == "ValidationError"
            assert "nan" in got.error_message

    def test_running_to_blocked_preserves_source_error(self, session_factory):
        with session_factory() as s:
            run = create_ingestion_run(s, source="imd", started_at=NOW)
            s.commit()
            update_ingestion_run(s, run.id, status="BLOCKED", completed_at=NOW,
                                 rows_received=0, rows_inserted=0, rows_rejected=0,
                                 error_type="SourceUnavailableError",
                                 error_message="IMD returned status=200 bytes=0 for year=2026")
            s.commit()
            got = get_ingestion_run(s, run.id)
            assert got.status == "BLOCKED"
            assert got.error_type == "SourceUnavailableError"
            assert "bytes=0" in got.error_message

    def test_latest_runs_ordered(self, session_factory):
        with session_factory() as s:
            a = create_ingestion_run(s, source="imd", started_at=NOW - timedelta(hours=2))
            b = create_ingestion_run(s, source="mock-sim", started_at=NOW)
            s.commit()
            rows = get_latest_ingestion_runs(s, limit=5)
            assert [r.id for r in rows] == [b.id, a.id]


# ------------------------------------------------------------ J1 pipeline integration
class _DownSource(ObservationSource):
    name = "imd"
    is_mock = False

    def __init__(self):
        self.attempts = 0

    def fetch(self, now=None):
        self.attempts += 1
        raise SourceUnavailableError("connection refused (simulated IMD outage)")

    def describe(self):
        return {"name": "imd", "product": "simulated-down"}


class TestJ1PipelineIntegration:
    def test_imd_unavailable_records_blocked_run_zero_observations(
            self, session_factory, seeded_cells):
        mapper = CellMapper(build_cells())
        pipeline = IngestionPipeline(_DownSource(), mapper, max_retries=1)
        with session_factory() as s:
            summary = pipeline.run(s, now=NOW)
            rid = int(summary["run_id"])

            run = get_ingestion_run(s, rid)
            assert run.status == RUN_BLOCKED
            assert run.error_type == "SourceUnavailableError"
            assert "connection refused" in run.error_message
            assert run.rows_received == 0 and run.rows_inserted == 0
            assert count_observations(s) == 0
            assert get_latest_ingestion_runs(s, 1)[0].id == rid

    def test_mock_path_persists_deterministic_observations(self, session_factory,
                                                           seeded_cells):
        mapper = CellMapper(build_cells())
        src = MockObservationSource(build_cells(), observation_date=NOW.date())
        pipeline = IngestionPipeline(src, mapper, allow_mock=True)
        with session_factory() as s:
            summary = pipeline.run(s, now=NOW)
            assert summary["recorded_status"] == RUN_SUCCESS
            assert summary["inserted"] == 4
            run = get_ingestion_run(s, summary["run_id"])
            assert run.status == RUN_SUCCESS
            assert run.source == "mock-sim"
            assert run.run_metadata["source_is_mock"] is True
            assert count_observations(s) == 4

        with session_factory() as s:
            rows = get_observation_history(s, "10.00_76.25")
            assert len(rows) == 1
            assert rows[0].source == "mock-sim"
            assert rows[0].quality_flag == QUALITY_VALID
            assert rows[0].observation_time.tzinfo is not None

    def test_mock_path_is_idempotent_across_runs(self, session_factory, seeded_cells):
        mapper = CellMapper(build_cells())
        src = MockObservationSource(build_cells(), observation_date=NOW.date())
        pipeline = IngestionPipeline(src, mapper, allow_mock=True)
        with session_factory() as s:
            a = pipeline.run(s, now=NOW)
            b = pipeline.run(s, now=NOW + timedelta(minutes=5))
            assert a["inserted"] == 4
            assert b["inserted"] == 0  # identical observations -> nothing duplicated
            assert count_observations(s) == 4
            runs = get_latest_ingestion_runs(s, 2)
            assert {r.status for r in runs} == {RUN_SUCCESS}

    def test_mock_guard_blocks_without_allow_mock(self, session_factory, seeded_cells):
        mapper = CellMapper(build_cells())
        src = MockObservationSource(build_cells(), observation_date=NOW.date())
        pipeline = IngestionPipeline(src, mapper, allow_mock=False)
        with session_factory() as s:
            summary = pipeline.run(s, now=NOW)
            assert summary["recorded_status"] == RUN_FAILED
            run = get_ingestion_run(s, summary["run_id"])
            assert run.status == RUN_FAILED
            assert run.error_type == "ConfigurationError"
            assert "MOCK" in run.error_message
            assert count_observations(s) == 0