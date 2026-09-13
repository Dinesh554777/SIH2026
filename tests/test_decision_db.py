"""Decision-layer database tests (live PostgreSQL, migration 0004).

Skipped when no PostgreSQL test DSN is reachable (same convention as
tests/test_geography_db.py). Rebuilds an EMPTY schema twice at head to prove
empty-init reproducibility, then exercises the decision-repository writes and
integrity guards.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database.config import test_database_url as _test_dsn
from src.database.db import _engine_for, ping_test
from src.database.decision_repository import (DecisionIntegrityError,
                                              latest_risk_assessment,
                                              record_advisory_delivery,
                                              record_monsoon_event,
                                              record_risk_assessment,
                                              upsert_agricultural_context)
from src.database.models import Base, RiskAssessment

pytestmark = pytest.mark.skipif(
    not (_test_dsn() and ping_test()),
    reason="PostgreSQL test database unavailable (see .env.example / scripts/setup_pg_db.sql)")

DECISION_TABLES = {
    "risk_assessments", "agricultural_context", "advisory_deliveries",
    "monsoon_events",
}


@pytest.fixture(scope="module")
def engine():
    url = _test_dsn()
    eng = _engine_for(url)
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    os.environ["DATABASE_URL"] = url
    try:
        for _ in range(2):  # twice: empty-init reproducibility at head
            with eng.connect() as conn:
                conn.execute(text("DROP SCHEMA public CASCADE"))
                conn.execute(text("CREATE SCHEMA public"))
                conn.commit()
            command.upgrade(cfg, "head")
        with eng.connect() as conn:
            assert conn.execute(text(
                "SELECT version_num FROM alembic_version")).scalar_one() == "0004"
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
            "TRUNCATE monsoon_events, advisory_deliveries, agricultural_context, "
            "risk_assessments RESTART IDENTITY CASCADE"))
        s.commit()


def test_head_is_0004_and_product_tables_present(session_factory):
    with session_factory() as s:
        v = s.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        names = {r[0] for r in s.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public'")).all()}
    assert v == "0004"
    assert DECISION_TABLES <= names


def test_risk_assessment_roundtrip(session_factory):
    with session_factory() as s:
        ra_id = record_risk_assessment(
            s, location_type="cell", location_id="10.75_77.5",
            decision="WAIT", confidence="medium", monsoon_status="onset_unstable",
            false_onset_risk="high", onset_probability=0.25,
            dry_spell_probability=0.7, break_probability=0.2,
            risk_summary={"onset": {"band": "low"}},
            evidence=[{"claim": "rain spike", "status": True, "detail": "40.1 mm"}],
            thresholds_version="1.0.0", mode="prototype/demo")
        s.commit()
    with session_factory() as s:
        latest = latest_risk_assessment(s, "cell", "10.75_77.5")
        assert latest is not None
        assert latest.decision == "WAIT"
        assert float(latest.onset_probability) == 0.25


def test_advisory_delivery_roundtrip(session_factory):
    with session_factory() as s:
        ra_id = record_risk_assessment(
            s, location_type="village", location_id="demo_001",
            decision="SOW", confidence="high", monsoon_status="onset_stable",
            false_onset_risk="low", onset_probability=0.7,
            dry_spell_probability=0.15, break_probability=0.1,
            risk_summary={}, evidence=[], thresholds_version="1.0.0")
        d1 = record_advisory_delivery(
            s, risk_assessment_id=ra_id, location_type="village",
            location_id="demo_001", decision="SOW", channel="notice_print",
            language="en,ta", status="generated",
            recipient_scope="Village", issued_by="agri_officer",
            payload={"channel": "notice_print"}, mock_notice="[MOCK]")
        d2 = record_advisory_delivery(
            s, risk_assessment_id=ra_id, location_type="village",
            location_id="demo_001", decision="SOW", channel="ivr",
            language="ta", status="generated")
        s.commit()
        assert d1 > 0 and d2 > 0


def test_agricultural_context_upsert_idempotent(session_factory):
    with session_factory() as s:
        upsert_agricultural_context(
            s, location_type="village", location_id="demo_001",
            crop="paddy", season="kharif", sowing_window_start="Jun-15",
            sowing_window_end="Jul-15", sow_confidence_needed=0.6,
            dry_spell_sensitivity="high", irrigation_availability="canal_optional",
            rainfall_requirement_mm=400)
        upsert_agricultural_context(
            s, location_type="village", location_id="demo_001",
            crop="paddy", season="kharif", sowing_window_start="Jun-15",
            sowing_window_end="Jul-15", sow_confidence_needed=0.65,
            dry_spell_sensitivity="high", irrigation_availability="canal_optional")
        s.commit()
    with session_factory() as s:
        rows = s.execute(text(
            "SELECT sow_confidence_needed FROM agricultural_context "
            "WHERE location_id='demo_001' AND crop='paddy'")).all()
    assert len(rows) == 1
    assert float(rows[0][0]) == 0.65


def test_monsoon_event_roundtrip(session_factory):
    with session_factory() as s:
        eid = record_monsoon_event(
            s, location_type="cell", location_id="10.75_77.5",
            event_type="false_onset", start_date=datetime(2024, 6, 7, tzinfo=timezone.utc),
            risk_level="high", note="rain spike then drying",
            source="decision-engine")
        s.commit()
        assert eid > 0


def test_integrity_guards_fail_loud(session_factory):
    with pytest.raises(DecisionIntegrityError):
        record_risk_assessment(
            None, location_type="continent", location_id="x",
            decision="SOW", confidence="high", monsoon_status="onset_stable",
            false_onset_risk="low", onset_probability=0.7,
            dry_spell_probability=0.1, break_probability=0.1,
            risk_summary={}, evidence=[], thresholds_version="1.0.0")
    with pytest.raises(DecisionIntegrityError):
        record_advisory_delivery(
            None, risk_assessment_id=1, location_type="village",
            location_id="a", decision="SOW", channel="esp", language="en")


def test_orm_constraint_backstops_bad_decision(session_factory):
    with session_factory() as s:
        with pytest.raises(IntegrityError):
            s.add(RiskAssessment(
                location_type="village", location_id="bad",
                decision="PLANT_NOW", confidence="high",
                monsoon_status="onset_stable", false_onset_risk="low",
                onset_probability=0.5, dry_spell_probability=0.1,
                break_probability=0.1, thresholds_version="1.0.0"))
            s.commit()