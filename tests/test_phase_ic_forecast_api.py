"""Phase I-C forecast API tests: frozen ML inference contract.

Covers: valid/invalid cell, forecast shape, determinism, provenance,
calibration, historical mode (never labelled live), /api/v1/model-info,
and optional PostgreSQL persistence (skipped when the DB is unavailable).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.serving.api import create_app  # noqa: E402
from src.serving.models import ModelService  # noqa: E402
from src.serving.registry import CellRegistry  # noqa: E402
from src.serving.store import ObservationStore  # noqa: E402

DEMO_CELL = "10.75_77.5"
EXPECTED_REVIVAL = 0.6047
TARGETS = ("onset", "break", "revival", "dry_spell")


def _build_client() -> TestClient:
    store = ObservationStore.from_file()
    registry = CellRegistry.from_matrix(store.matrix)
    service = ModelService(store, matrix=store.matrix)
    return TestClient(create_app(store=store, registry=registry, service=service))


@pytest.fixture(scope="module")
def client():
    return _build_client()


def _forecast(client: TestClient, date: str = "2024-08-12") -> dict:
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/forecast", params={"date": date})
    assert r.status_code == 200, r.text
    return r.json()


# -------------------------------------------------------------------- cells
def test_valid_cell_listed(client):
    r = client.get("/api/v1/cells")
    assert r.status_code == 200
    d = r.json()
    assert d["count"] == 304
    assert DEMO_CELL in {c["cell_id"] for c in d["cells"]}


def test_invalid_cell_404(client):
    r = client.get("/api/v1/cells/99.99_99.99/forecast")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "unknown_cell"


def test_invalid_cell_on_malformed_id(client):
    for bad in ("99.99_99.99", "not_a_cell", "10.75"):
        r = client.get(f"/api/v1/cells/{bad}/forecast")
        assert r.status_code == 404, bad


# ------------------------------------------------------------------ forecast
def test_forecast_contract_shape(client):
    d = _forecast(client)
    assert d["cell_id"] == DEMO_CELL
    assert d["forecast_date"] == "2024-08-12"
    assert set(d["probabilities"].keys()) == set(TARGETS)
    assert all(0.0 <= d["probabilities"][t] <= 1.0 for t in TARGETS)
    assert abs(d["probabilities"]["revival"] - EXPECTED_REVIVAL) < 1e-4
    # probabilities == target cards (single source of truth)
    for t in TARGETS:
        assert abs(d["probabilities"][t] - d["targets"][t]["probability"]) < 1e-12
    assert set(d["models"].keys()) == set(TARGETS)
    assert set(d["calibration"].keys()) == set(TARGETS)


def test_forecast_model_strategy(client):
    d = _forecast(client)
    assert d["models"]["onset"] == {"model": "persistence", "feature_group": "frozen_reference"}
    assert d["models"]["break"] == {"model": "persistence", "feature_group": "frozen_reference"}
    assert d["models"]["dry_spell"] == {"model": "persistence", "feature_group": "frozen_reference"}
    assert d["models"]["revival"]["model"] == "xgboost"
    assert d["models"]["revival"]["feature_group"] == "B_temporal"
    assert d["models"]["revival"]["n_features"] == 64


def test_forecast_deterministic(client):
    a = _forecast(client)
    b = _forecast(client)
    mask = lambda dd: {k: v for k, v in dd.items()
                       if k not in ("generated_at", "persistence")}
    assert mask(a) == mask(b)


def test_forecast_matches_frozen_regression(client):
    d = _forecast(client)
    # persistence targets are frozen climatology/transition probabilities
    assert abs(d["probabilities"]["revival"] - EXPECTED_REVIVAL) < 1e-4
    assert d["generated_at"].endswith("Z")
    assert d["observations_used"]["imd_sum14"] is not None


def test_forecast_no_hardcoded_values(client):
    d = _forecast(client)
    # a second, unrelated pivot must differ (real inference, not canned numbers)
    other = _forecast(client, date="2024-09-29")
    assert d["probabilities"] != other["probabilities"]
    assert abs(d["probabilities"]["revival"] - other["probabilities"]["revival"]) > 0


# ---------------------------------------------------------------- provenance
def test_forecast_provenance(client):
    d = _forecast(client)
    p = d["provenance"]
    assert p["freeze_digest"]
    assert p["train_period"] and p["validation_period"] and p["test_period"]
    assert p["note"].startswith("2024 TEST DATA WAS NOT USED") or "TEST DATA WAS NOT USED" in p["note"]


def test_provenance_matches_model_info(client):
    d = _forecast(client)
    mi = client.get("/api/v1/model-info").json()
    assert mi["freeze_digest"] == d["provenance"]["freeze_digest"]
    assert mi["model_version"] == d["provenance"].get("model_version", mi["model_version"])


# ---------------------------------------------------------------- calibration
def test_forecast_calibration(client):
    d = _forecast(client)
    for t in TARGETS:
        c = d["calibration"][t]
        assert {"ece", "brier"} <= set(c)
        assert isinstance(c["ece"], float)
        assert c["brier"] >= 0.0
    assert [x["state"] for x in d["confidence"]["calibration"]] == list(TARGETS)


# ------------------------------------------------------------------ historical
def test_historical_mode_never_live(client):
    d = _forecast(client)
    assert d["mode"] == "historical"
    assert d["data_mode"] == "historical/demo"
    assert "live" not in d["mode"]
    assert d["persistence"]["mode"] == "historical"


def test_model_info_historical(client):
    mi = client.get("/api/v1/model-info").json()
    assert mi["mode"] == "historical"
    assert mi["data_mode"] == "historical/demo"


def test_model_info_endpoint(client):
    r = client.get("/api/v1/model-info")
    assert r.status_code == 200
    d = r.json()
    assert d["freeze_digest"]
    assert d["models"]["revival"]["strategy"] == "xgboost_groupB"
    assert d["models"]["onset"]["strategy"] == "persistence"
    assert d["models"]["revival"]["n_features"] == 64
    assert "artifact" in d["models"]["revival"]
    assert "ece" in d["calibration"]["onset"] and "brier" in d["calibration"]["onset"]


# ------------------------------------------------------------ DB persistence
def _migrate_and_seed(monkeypatch, url: str) -> None:
    from sqlalchemy import text

    from alembic import command
    from alembic.config import Config

    from src.database.db import session_factory, _engine_for
    from src.database.repository import seed_cells, seed_model_metadata
    from src.database.seed import load_cells, load_freeze

    # The endpoint + env.py resolve the DSN via database_url() -> DATABASE_URL.
    monkeypatch.setenv("DATABASE_URL", url)

    engine = _engine_for(url)
    with engine.connect() as conn:
        # Recreate an empty schema from any prior state (test_database.py may
        # share this DB), then migrate it.
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(cfg, "head")

    cells = load_cells()
    freeze, digest = load_freeze()
    with session_factory(engine)() as s:
        seed_cells(s, cells)
        seed_model_metadata(s, freeze, digest)
        s.execute(text("TRUNCATE advisories, forecasts RESTART IDENTITY CASCADE"))
        s.commit()


def test_forecast_persists_to_database(monkeypatch):
    from src.database.config import test_database_url
    from src.database.db import ping, session_factory, _engine_for
    from src.database.repository import get_advisories, get_forecasts_for_cell

    dsn = test_database_url()
    if not (dsn and ping(dsn)):
        pytest.skip("PostgreSQL test database unavailable - persistence not exercised")

    _migrate_and_seed(monkeypatch, dsn)

    client = _build_client()
    d = _forecast(client)
    info = d["persistence"]
    assert info["persisted"] is True, info
    assert info["database"] == "postgresql"

    with session_factory(_engine_for(dsn))() as s:
        rows = get_forecasts_for_cell(s, DEMO_CELL)
        assert rows, "no forecast rows persisted"
        target = [f for f in rows
                  if pd.Timestamp(f.forecast_date).date().isoformat() == "2024-08-12"]
        assert target, "2024-08-12 forecast not found after persistence"
        assert abs(float(target[0].revival_probability) - EXPECTED_REVIVAL) < 1e-3
        advisories = get_advisories(s, target[0].id)
        assert len(advisories) == 5
        assert {a.advisory_type for a in advisories} == {"summary", "card"}


def test_forecast_persistence_is_best_effort(client):
    # The endpoint must answer 200 with a truthful persistence block whether or
    # not the database is reachable/configured (never a 500, never a fake "ok").
    d = _forecast(client)
    info = d["persistence"]
    assert isinstance(info["persisted"], bool)
    assert info["database"] == "postgresql"
    assert isinstance(info["note"], str) and info["note"]
    if info["persisted"]:
        assert info["note"].startswith("inserted")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))