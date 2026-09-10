"""MVP API + scientific integrity tests.

Run:  python -m pytest tests/test_mvp_api.py tests/test_mvp_integrity.py -q
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


@pytest.fixture(scope="module")
def store():
    return ObservationStore.from_file()


@pytest.fixture(scope="module")
def client():
    store = ObservationStore.from_file()
    registry = CellRegistry.from_matrix(store.matrix)
    service = ModelService(store, matrix=store.matrix)
    app = create_app(store=store, registry=registry, service=service)
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok"
    assert d["data_mode"] == "historical/demo"
    assert d["freeze_digest"]


def test_locations(client):
    r = client.get("/locations")
    assert r.status_code == 200
    locs = r.json()["locations"]
    assert len(locs) == 304
    assert {l["region"] for l in locs} == {"TN", "MH", "KA"}
    assert all(l["admin_note"] == "grid_cell_only" for l in locs)


def test_location_single(client):
    r = client.get(f"/locations/{DEMO_CELL}")
    assert r.status_code == 200
    loc = r.json()["location"]
    assert loc["cell_id"] == DEMO_CELL
    assert "observation_period" in loc


def test_forecast_ok(client):
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/forecast", params={"date": "2024-08-12"})
    assert r.status_code == 200
    d = r.json()
    assert d["cell_id"] == DEMO_CELL
    assert d["forecast_date"] == "2024-08-12"
    assert set(d["targets"].keys()) == {"onset", "break", "revival", "dry_spell"}
    assert abs(d["targets"]["revival"]["probability"] - 0.6047) < 1e-3
    assert d["provenance"]["note"].startswith("2024 TEST DATA WAS NOT USED")
    assert d["data_mode"] == "historical/demo"


def test_forecast_matches_direct_inference(client):
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/forecast", params={"date": "2024-08-12"})
    d = r.json()
    store = ObservationStore.from_file()
    service = ModelService(store, matrix=store.matrix)
    pred = service.predict(DEMO_CELL, pd.Timestamp("2024-08-12"))
    for t in ("onset", "break", "revival", "dry_spell"):
        assert abs(d["targets"][t]["probability"] - pred[t]["probability"]) < 1e-9


def test_forecast_default_latest(client):
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/forecast")
    assert r.status_code == 200
    assert r.json()["forecast_date"] == "2024-09-30"


def test_advisory_ok(client):
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/advisory", params={"date": "2024-08-12"})
    assert r.status_code == 200
    d = r.json()
    assert d["dominant_state"] in ("onset", "break", "revival", "dry_spell")
    assert len(d["items"]) == 4
    assert any("expert" in it["expert_validation"] for it in d["items"])
    assert d["disclaimer"]
    assert d["summary"]


def test_explain_ok(client):
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/explain", params={"date": "2024-08-12"})
    assert r.status_code == 200
    d = r.json()
    assert d["target"] == "revival"
    assert any(s["feature"] == "th_accel" for s in d["sensitivity"])
    assert "causal" not in d["caveat"].lower() or "not" in d["caveat"].lower()


def test_unknown_cell_404(client):
    r = client.get("/api/v1/cells/99.99_99.99/forecast")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "unknown_cell"


def test_malformed_cell_404(client):
    r = client.get('/api/v1/cells/../../etc/forecast')
    assert r.status_code == 404


def test_malformed_date_422(client):
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/forecast", params={"date": "notadate"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_date"


def test_outside_season_422(client):
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/forecast", params={"date": "2024-12-31"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "outside_season"


def test_date_not_available_404(client):
    # JJAS date before the pilot data window (starts 2015-06-01)
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/forecast", params={"date": "2014-06-15"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "date_not_available"


def test_invalid_cell_not_present(client):
    r = client.get("/api/v1/cells/10.5_100.0/forecast")
    assert r.status_code == 404


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))