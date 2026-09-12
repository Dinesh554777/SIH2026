"""Database tests (Phase I-B STEP: TESTING).

Run against the test database (DATABASE_URL_TEST, default <app dbname>_test).
The entire module is skipped when no PostgreSQL test DSN is configured/reachable,
so `pytest` keeps passing in CI without a database. Provisioning + DSN:
see scripts/setup_pg_db.sql and .env.example.

Each run exercises the migration path on an EMPTY database (drop_all on teardown),
proving reproducibility: empty DB -> alembic upgrade head -> seed -> app works.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database.db import _engine_for, ping_test
from src.database.models import (Advisory, Base, Cell, Forecast, ModelMetadata)
from src.database.repository import (count_rows, get_advisories,
                                     get_forecasts_for_cell, seed_cells,
                                     seed_model_metadata, store_forecast_bundle,
                                     table_names, upsert_forecast)
from src.database.config import test_database_url
from src.database.seed import load_cells, load_freeze

EXPECTED_TABLES = {"cells", "model_metadata", "forecasts", "advisories"}

pytestmark = pytest.mark.skipif(
    not (test_database_url() and ping_test()),
    reason="PostgreSQL test database unavailable (see .env.example / scripts/setup_pg_db.sql)")


@pytest.fixture(scope="module")
def engine():
    url = test_database_url()
    eng = _engine_for(url)

    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)

    with eng.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
    command.upgrade(cfg, "head")

    with eng.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    command.upgrade(cfg, "head")  # freshly empty -> proves empty-init reproducibility

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
        s.execute(text("TRUNCATE advisories, forecasts, model_metadata, "
                       "cells RESTART IDENTITY CASCADE"))
        s.commit()


@pytest.fixture(scope="module")
def source():
    cells = load_cells()
    freeze, digest = load_freeze()
    return cells, freeze, digest


@pytest.fixture(scope="module")
def mini_cell(source) -> dict:
    cells, _, _ = source
    r = cells.iloc[0]
    return {"cell_id": str(r["cell_id"]), "latitude": float(r["lat"]),
            "longitude": float(r["lon"]), "region": str(r["region"])}


def _mk_cell(session_factory, cell: dict):
    with session_factory() as s:
        s.add(Cell(**cell))
        s.commit()


def _mk_model(session_factory, digest, target="onset"):
    with session_factory() as s:
        s.add(ModelMetadata(model_name="persistence", target=target,
                            version="FREEZE_H", feature_group="frozen_reference",
                            training_period="2015-2021", validation_period="2022-2023",
                            test_period="2024", artifact_digest=digest))
        s.commit()
        return s.execute(
            text("SELECT id FROM model_metadata WHERE target = :t AND artifact_digest = :d"),
            {"t": target, "d": digest}).scalar_one()


def _probs(digest: str) -> dict:
    return {"cell_id": "10.75_77.5", "forecast_date": "2024-08-12",
            "onset_probability": 0.1, "break_probability": 0.2,
            "revival_probability": 0.3, "dry_spell_probability": 0.4,
            "model_version": digest, "mode": "historical/demo"}


BUNDLE = {
    "dominant": "dry_spell",
    "cards": [
        {"state": t, "state_label": t, "probability": p, "probability_pct": p * 100,
         "band": "low", "band_meaning": "Unlikely", "interpretation": f"interpretation-{t}",
         "suggested_action": f"action-{t}", "expert_validation": "v"}
        for t, p in [("onset", 0.05), ("break", 0.10), ("revival", 0.15),
                     ("dry_spell", 0.35)]
    ],
    "current_signal": {"rain_t_mm": 0.0, "rainfall_trend": "Stable"},
    "disclaimer": "x",
    "evidence": {"imd_rain_t": 0.0},
}


# --------------------------------------------------------------------------
def test_connection_ok(session_factory):
    with session_factory() as s:
        assert s.execute(text("SELECT 1")).scalar_one() == 1


def test_empty_init_creates_all_tables(session_factory):
    with session_factory() as s:
        names = set(table_names(s))
    assert EXPECTED_TABLES <= names


def test_seed_304_cells_from_registry(session_factory, source):
    cells, freeze, digest = source
    with session_factory() as s:
        seeded = seed_cells(s, cells)
        metadata_rows = seed_model_metadata(s, freeze, digest)
        assert count_rows(s, Cell) == 304
    assert seeded == 304
    assert metadata_rows == 4


def test_region_is_bbox_derived(session_factory, source):
    cells, _, _ = source
    with session_factory() as s:
        seed_cells(s, cells)
        regions = s.execute(
            text("SELECT DISTINCT region FROM cells ORDER BY region")).scalars().all()
    assert regions == sorted(cells["region"].dropna().unique().tolist())


def test_cell_lookup(session_factory, mini_cell):
    _mk_cell(session_factory, mini_cell)
    with session_factory() as s:
        row = s.execute(text("SELECT * FROM cells WHERE cell_id = :c"),
                        {"c": mini_cell["cell_id"]}).mappings().one()
    assert row["latitude"] == pytest.approx(mini_cell["latitude"])
    assert row["region"] == mini_cell["region"]
    assert row["state"] is None  # reserved; never claimed as admin boundary


def test_cells_unique_constraint(session_factory, mini_cell):
    _mk_cell(session_factory, mini_cell)
    with session_factory() as s:
        with pytest.raises(IntegrityError):
            s.add(Cell(**mini_cell))
            s.commit()
        s.rollback()
        assert count_rows(s, Cell) == 1


def test_model_metadata_seed_matches_freeze(session_factory, source):
    cells, freeze, digest = source
    with session_factory() as s:
        seed_cells(s, cells)
        result = seed_model_metadata(s, freeze, digest)
        seed_model_metadata(s, freeze, digest)  # idempotent second pass
        rows = s.execute(text(
            "SELECT target, model_name, version, feature_group, artifact_digest "
            "FROM model_metadata ORDER BY target")).mappings().all()
    by_target = {r["target"]: r for r in rows}
    assert by_target["onset"]["model_name"] == freeze["targets"]["onset"]["selected_model"]
    assert by_target["revival"]["feature_group"] == freeze["targets"]["revival"]["feature_group"]
    assert all(r["artifact_digest"] == digest for r in rows)
    assert all(r["version"] == "FREEZE_H" for r in rows)
    assert {r["target"] for r in rows} == {"onset", "break", "revival", "dry_spell"}
    assert len(rows) == 4
    assert result == 4


def test_forecast_insert_and_retrieve(session_factory, mini_cell, source):
    cells, freeze, digest = source
    _mk_cell(session_factory, mini_cell)
    _mk_model(session_factory, digest)
    with session_factory() as s:
        seed_cells(s, cells)
        fid = upsert_forecast(s, **_probs(digest))
        f = s.get(Forecast, fid)
    assert float(f.revival_probability) == pytest.approx(0.3)
    assert f.model_version == digest
    assert f.mode == "historical/demo"


def test_upsert_forecast_idempotent(session_factory, mini_cell, source):
    _, _, digest = source
    _mk_cell(session_factory, mini_cell)
    with session_factory() as s:
        a = upsert_forecast(s, **_probs(digest))
        b = upsert_forecast(s, **_probs(digest))
        assert a == b
        assert count_rows(s, Forecast) == 1


def test_forecast_probability_check_rejects_out_of_range(session_factory, mini_cell, source):
    _, _, digest = source
    _mk_cell(session_factory, mini_cell)
    kw = _probs(digest)
    kw["onset_probability"] = 1.5
    with session_factory() as s:
        with pytest.raises(IntegrityError):
            upsert_forecast(s, **kw)
            s.commit()
        s.rollback()


def test_forecast_fk_restricts_unknown_cell(session_factory, source):
    _, _, digest = source
    with session_factory() as s:
        with pytest.raises(IntegrityError):
            upsert_forecast(s, **_probs(digest))
            s.commit()
        s.rollback()


def test_bundle_persists_summary_plus_four_cards(session_factory, mini_cell, source):
    _, _, digest = source
    _mk_cell(session_factory, mini_cell)
    with session_factory() as s:
        fid = store_forecast_bundle(
            s, cell_id=mini_cell["cell_id"], forecast_date="2024-08-12",
            probabilities={"onset": .1, "break": .2, "revival": .3, "dry_spell": .4},
            model_version=digest, bundle=BUNDLE)
        advisories = get_advisories(s, fid)
        assert {a.advisory_type for a in advisories} == {"summary", "card"}
        assert sum(1 for a in advisories if a.advisory_type == "summary") == 1
        assert sum(1 for a in advisories if a.advisory_type == "card") == 4
        assert all(a.language == "en" for a in advisories)
        cards = [a for a in advisories if a.advisory_type == "card"]
        assert any("interpretation-dry_spell" in a.message for a in cards)


def test_advisories_cascade_on_forecast_delete(session_factory, mini_cell, source):
    _, _, digest = source
    _mk_cell(session_factory, mini_cell)
    with session_factory() as s:
        fid = store_forecast_bundle(
            s, cell_id=mini_cell["cell_id"], forecast_date="2024-08-13",
            probabilities={"onset": .1, "break": .2, "revival": .3, "dry_spell": .4},
            model_version=digest, bundle=BUNDLE)
        assert count_rows(s, Advisory) == 5
        s.execute(text("DELETE FROM forecasts WHERE id = :fid"), {"fid": fid})
        s.commit()
        assert count_rows(s, Advisory) == 0


def test_retrieval_orders_by_date_desc(session_factory, mini_cell, source):
    _, _, digest = source
    _mk_cell(session_factory, mini_cell)
    with session_factory() as s:
        for d in ("2024-06-05", "2024-08-12", "2024-07-20"):
            kw = _probs(digest)
            kw["cell_id"] = mini_cell["cell_id"]
            kw["forecast_date"] = d
            upsert_forecast(s, **kw)
        rows = get_forecasts_for_cell(s, mini_cell["cell_id"])
        dates = [pd.Timestamp(f.forecast_date).date().isoformat() for f in rows]
    assert dates == ["2024-08-12", "2024-07-20", "2024-06-05"]


def test_generated_at_is_aware_utc(session_factory, mini_cell, source):
    _, _, digest = source
    _mk_cell(session_factory, mini_cell)
    with session_factory() as s:
        fid = upsert_forecast(s, cell_id=mini_cell["cell_id"], forecast_date="2024-08-14",
                              onset_probability=.1, break_probability=.2,
                              revival_probability=.3, dry_spell_probability=.4,
                              model_version=digest)
        ga = s.execute(text("SELECT generated_at FROM forecasts WHERE id = :fid"),
                       {"fid": fid}).scalar_one()
    assert ga.tzinfo is not None


def test_reference_record_roundtrip(session_factory, source):
    cells, freeze, digest = source
    from src.database.seed import seed
    from src.serving.demo import DEMO_CELL, EXPECTED_REVIVAL_2024_08_12
    with session_factory() as s:
        seed(s, cells, freeze, digest)
        fid = store_forecast_bundle(
            s, cell_id=DEMO_CELL, forecast_date="2024-08-12",
            probabilities={"onset": .0, "break": .0, "revival": EXPECTED_REVIVAL_2024_08_12,
                           "dry_spell": .0},
            model_version=digest, bundle=BUNDLE)
        f = s.get(Forecast, fid)
    assert float(f.revival_probability) == pytest.approx(EXPECTED_REVIVAL_2024_08_12, abs=1e-3)
    assert f.cell_id == DEMO_CELL


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))