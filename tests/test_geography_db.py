"""Geography database tests (live PostgreSQL, migration 0003).

Skipped entirely when no PostgreSQL test DSN is configured/reachable (the same
convention as tests/test_database.py). Each run rebuilds an EMPTY schema and
upgrades to head (0003) twice, proving empty-init reproducibility and that the
scientific `cells` registry survives the geography migration untouched.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database.config import test_database_url as _test_dsn
from src.database.db import _engine_for, ping_test
from src.database.geography_repository import (assert_mapping_references,
                                               children, count_geography,
                                               count_mappings,
                                               geography_availability,
                                               import_boundaries,
                                               list_geography, upsert_entity,
                                               upsert_mapping)
from src.database.models import Base, Cell
from src.database.repository import count_rows, seed_cells
from src.database.seed import load_cells

pytestmark = pytest.mark.skipif(
    not (_test_dsn() and ping_test()),
    reason="PostgreSQL test database unavailable (see .env.example / scripts/setup_pg_db.sql)")

GEO_TABLES = {"states", "districts", "blocks", "villages",
              "geography_grid_mapping"}


@pytest.fixture(scope="module")
def engine():
    url = _test_dsn()
    eng = _engine_for(url)
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    os.environ["DATABASE_URL"] = url
    try:
        for _ in range(2):  # twice: empty-init reproducibility at 0003
            with eng.connect() as conn:
                conn.execute(text("DROP SCHEMA public CASCADE"))
                conn.execute(text("CREATE SCHEMA public"))
                conn.commit()
            command.upgrade(cfg, "head")
        with eng.connect() as conn:
            assert conn.execute(text(
                "SELECT version_num FROM alembic_version")).scalar_one() == "0003"
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
        s.execute(text(
            "TRUNCATE geography_grid_mapping, villages, blocks, districts, "
            "states, observations, ingestion_runs, advisories, forecasts, "
            "model_metadata, cells RESTART IDENTITY CASCADE"))
        s.commit()


def _seed_cells(session_factory) -> int:
    cells = load_cells()
    with session_factory() as s:
        n = seed_cells(s, cells)
        s.commit()
        return n


# ------------------------------------------------------------------ schema
def test_geography_tables_exist_after_migration(session_factory):
    with session_factory() as s:
        names = {r[0] for r in s.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public'")).all()}
    assert GEO_TABLES <= names
    assert {"cells", "forecasts", "observations", "ingestion_runs"} <= names


def test_head_is_0003(session_factory):
    with session_factory() as s:
        v = s.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert v == "0003"


# ------------------------------------------------------- scientific compat
def test_cells_registry_intact_after_migration(session_factory):
    n = _seed_cells(session_factory)
    assert n == 304
    with session_factory() as s:
        assert count_rows(s, Cell) == 304
        states_in_cells = s.execute(text(
            "SELECT state FROM cells GROUP BY state")).scalars().all()
    # `state` on cells stays NULL: reserved, never claimed as admin boundary
    assert states_in_cells == [None]


def test_forecast_schema_untouched(session_factory):
    with session_factory() as s:
        n_forecast_cols = s.execute(text(
            "SELECT count(*) FROM information_schema.columns "
            "WHERE table_name = 'forecasts'")).scalar_one()
    assert n_forecast_cols == 10


# ------------------------------------------------------------- repository
def test_entity_upsert_idempotent(session_factory):
    rec = {"geography_type": "state", "geography_id": "TN-01",
           "name": "Tamil Nadu", "parent_geography_id": None,
           "latitude": 11.1, "longitude": 79.0, "geometry_ref": "states:TN-01",
           "source": "AUTHORITATIVE-FIXTURE", "source_version": "2024.1"}
    with session_factory() as s:
        upsert_entity(s, "state", rec)
        upsert_entity(s, "state", rec)
        s.commit()
        assert count_geography(s, "state") == 1


def test_hierarchy_persistence(session_factory):
    with session_factory() as s:
        upsert_entity(s, "state", {"geography_id": "ST", "name": "S",
                                   "source": "x", "source_version": "1"})
        upsert_entity(s, "district", {"geography_id": "DI",
                                       "parent_geography_id": "ST",
                                       "name": "D", "source": "x",
                                       "source_version": "1"})
        upsert_entity(s, "block", {"geography_id": "BL",
                                    "parent_geography_id": "DI",
                                    "name": "B", "source": "x",
                                    "source_version": "1"})
        upsert_entity(s, "village", {"geography_id": "VI",
                                      "parent_geography_id": "BL",
                                      "name": "V", "source": "x",
                                      "source_version": "1"})
        s.commit()
        assert children(s, "state", "ST")[0]["geography_id"] == "DI"
        assert children(s, "district", "DI")[0]["geography_id"] == "BL"
        assert children(s, "block", "BL")[0]["geography_id"] == "VI"


def test_mapping_insert_and_reference_validation(session_factory):
    from src.geography.entities import GridToAdminMapping
    _seed_cells(session_factory)
    m = GridToAdminMapping(
        grid_cell_id="10.75_77.5", geography_type="block", geography_id="B",
        intersection_fraction=0.5, mapping_method="area_weighted_intersection",
        source="x", version="1", cell_area_deg2=0.0625,
        intersection_area_deg2=0.03125).record()
    with session_factory() as s:
        with pytest.raises(Exception) as exc:
            assert_mapping_references(s, m)  # block B absent -> must fail
        assert "unknown block" in str(exc.value)
        upsert_entity(s, "state", {"geography_id": "S2", "name": "st",
                                   "source": "x", "source_version": "1"})
        upsert_entity(s, "district", {"geography_id": "D2",
                                       "parent_geography_id": "S2",
                                       "name": "d", "source": "x",
                                       "source_version": "1"})
        upsert_entity(s, "block", {"geography_id": "B",
                                    "parent_geography_id": "D2",
                                    "name": "b", "source": "x",
                                    "source_version": "1"})
        upsert_mapping(s, m)
        s.commit()
        assert count_mappings(s) == 1
        upsert_mapping(s, m)  # idempotent ON CONFLICT DO NOTHING
        s.commit()
        assert count_mappings(s) == 1


def test_mapping_fraction_check_rejects_out_of_range(session_factory):
    _seed_cells(session_factory)
    rec = {"grid_cell_id": "10.75_77.5", "geography_type": "block",
           "geography_id": "B", "intersection_fraction": 1.5,
           "mapping_method": "area_weighted_intersection",
           "source": "x", "version": "1"}
    with session_factory() as s:
        with pytest.raises(IntegrityError):
            upsert_mapping(s, rec)
            s.commit()
        s.rollback()


def test_end_to_end_import_of_validated_bundle(session_factory, tmp_path):
    import tests.test_geography as G
    from src.geography.registry import GeographyRegistry
    _seed_cells(session_factory)
    cells = load_cells()
    ready = G.make_ready_bundle(tmp_path, cells)
    reg = GeographyRegistry(source_root=tmp_path / "sources", ready_root=ready)
    assert reg.boundaries_available
    with session_factory() as s:
        result = import_boundaries(s, reg)
    assert result["entities"] == {"state": 1, "district": 1, "block": 2,
                                  "village": 0}
    assert result["mappings_inserted"] > 0
    with session_factory() as s:
        assert count_geography(s, "block") == 2
        assert count_mappings(s) == result["mappings_inserted"]
        assert all(m["grid_cell_id"] in set(reg.cells["cell_id"])
                   for m in [dict(r) for r in s.execute(
                       text("SELECT grid_cell_id, geography_id FROM "
                            "geography_grid_mapping")).mappings()])
        blocks = list_geography(s, "block")
        assert {b["geography_id"] for b in blocks} == {"FIXTURE-BA", "FIXTURE-BB"}


def test_import_blocked_without_authoritative_bundle(session_factory, tmp_path):
    from src.geography.registry import GeographyRegistry
    reg = GeographyRegistry(source_root=tmp_path / "empty",
                            ready_root=tmp_path / "noready")
    assert reg.boundaries_available is False
    with session_factory() as s:
        result = import_boundaries(s, reg)
        assert result["available"] is False
        assert result["mappings_inserted"] == 0
        assert all(v == 0 for v in geography_availability(s).values())


# ------------------------------------------------------------------ reversible
def test_downgrade_to_0002_removes_geography_only(session_factory, engine):
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    url = _test_dsn()
    os.environ["DATABASE_URL"] = url
    try:
        command.downgrade(cfg, "0002")
        with engine.connect() as conn:
            names = {r[0] for r in conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'")).all()}
        assert not GEO_TABLES & names
        assert "cells" in names
        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            names = {r[0] for r in conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'")).all()}
        assert GEO_TABLES <= names
    finally:
        os.environ.pop("DATABASE_URL", None)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))