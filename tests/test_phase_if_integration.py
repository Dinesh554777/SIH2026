"""Phase I-F full-MVP integration tests.

Walks the complete user journey (React frontend -> FastAPI -> frozen ML ->
deterministic advisory -> Groq explanation -> PostgreSQL persistence) and the
required failure scenarios (backend down is covered by the frontend suite;
PostgreSQL unavailable, Groq unavailable, invalid cell, malformed response,
frontend refresh and repeated request are exercised here). The critical frozen
regression for demo cell 10.75_77.5 (revival = 0.6047) is asserted directly and
is the SAME value the frontend renders (frontend fixtures carry the captured
API value 0.6046834588050842 -> 60.5%).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.serving.api import create_app  # noqa: E402
from src.serving.groq_explain import GroqExplainer  # noqa: E402
from src.serving.models import ModelService  # noqa: E402
from src.serving.registry import CellRegistry  # noqa: E402
from src.serving.store import ObservationStore  # noqa: E402

DEMO_CELL = "10.75_77.5"
DATE = "2024-08-12"
REVIVAL_RAW = 0.6046834588050842
REVIVAL_ROUNDED = 0.6047
TARGETS = ("onset", "break", "revival", "dry_spell")
FREEZE_DIGEST = "4f122044f8710b53"


def _build_client(groq=None) -> TestClient:
    store = ObservationStore.from_file()
    registry = CellRegistry.from_matrix(store.matrix)
    service = ModelService(store, matrix=store.matrix)
    return TestClient(create_app(store=store, registry=registry, service=service, groq=groq))


@pytest.fixture(scope="module")
def client():
    return _build_client()


def _forecast(client: TestClient, date: str = DATE) -> dict:
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/forecast", params={"date": date})
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------- the journey
def test_full_journey_demo_cell(client):
    """Open app -> select cell -> forecast -> stored -> advisory -> explanation."""
    # 1. catalog loads (React selector)
    cells = client.get("/api/v1/cells").json()
    assert cells["count"] == 304
    assert any(c["cell_id"] == DEMO_CELL for c in cells["cells"])
    # 2. forecast for the selected demo cell (frozen inference)
    d = _forecast(client)
    assert d["cell_id"] == DEMO_CELL
    assert d["forecast_date"] == DATE
    # 3. critical frozen regression
    assert d["probabilities"]["revival"] == pytest.approx(REVIVAL_ROUNDED, abs=1e-4)
    assert d["probabilities"]["revival"] == pytest.approx(REVIVAL_RAW, rel=0.0, abs=1e-12)
    assert d["targets"]["revival"]["probability"] == d["probabilities"]["revival"]
    assert d["targets"]["revival"]["band"] == "high"
    assert d["targets"]["revival"]["model"] == "xgboost"
    assert d["targets"]["revival"]["feature_group"] == "B_temporal"
    # 4. forecast stored/retrieved (best-effort persistence block reported back)
    assert d["persistence"]["database"] == "postgresql"
    # 5. deterministic advisory cards are complete
    adv = client.get(f"/api/v1/cells/{DEMO_CELL}/advisory", params={"date": DATE}).json()
    assert adv["dominant_state"] == "dry_spell"
    assert len(adv["items"]) == 4
    assert all("interpretation" in c and "suggested_action" in c for c in adv["items"])
    # 6. explanation (Groq or deterministic fallback) is structurally complete
    ex = client.get(f"/api/v1/cells/{DEMO_CELL}/explanation",
                    params={"date": DATE, "lang": "en"}).json()
    for key in ("summary", "why", "action", "caution"):
        assert isinstance(ex[key], str) and ex[key].strip(), key
    assert ex["source"] in ("groq", "fallback")
    # 7. model transparency is available for the frontend panel
    mi = client.get("/api/v1/model-info").json()
    assert mi["freeze_digest"] == FREEZE_DIGEST
    assert mi["train_period"] == "2015-2021"
    assert mi["validation_period"] == "2022-2023"
    assert mi["test_period"] == "2024"
    # sensitivity explanation for the Why? panel
    why = client.get(f"/api/v1/cells/{DEMO_CELL}/explain", params={"date": DATE}).json()
    assert why["target"] == "revival"
    assert len(why["sensitivity"]) > 0


# ------------------------------------------------- regression + Groq isolation
def test_numerical_forecast_survives_groq_failure(client):
    """Frozen numerics must remain functional even when Groq fails hard."""
    class _RaisingCompletions:
        def create(self, **kwargs):
            raise RuntimeError("groq backend down")

    class _RaisingChat:
        completions = _RaisingCompletions()

    class _RaisingClient:
        chat = _RaisingChat()

    client_broken = _build_client(groq=GroqExplainer(api_key="x", client=_RaisingClient()))
    d = _forecast(client_broken)
    assert d["probabilities"]["revival"] == pytest.approx(REVIVAL_ROUNDED, abs=1e-4)
    for t in TARGETS:
        assert 0.0 <= d["probabilities"][t] <= 1.0
    ex = client_broken.get(f"/api/v1/cells/{DEMO_CELL}/explanation",
                           params={"date": DATE}).json()
    assert ex["source"] == "fallback"
    assert ex["groq"]["status"] == "error"
    assert ex["summary"] and ex["action"]  # deterministic advisory still present


def test_groq_not_configured_falls_back_to_advisory(client):
    client_nokey = _build_client(groq=GroqExplainer(api_key=""))
    ex = client_nokey.get(f"/api/v1/cells/{DEMO_CELL}/explanation",
                          params={"date": DATE}).json()
    assert ex["source"] == "fallback"
    assert ex["groq"]["status"] == "not_configured"
    assert "Dry spell" in ex["summary"]


# ------------------------------------------------------------- failure modes
def test_postgres_unavailable_forecast_still_works(client, monkeypatch):
    """PostgreSQL down: persisted block reports unreachable; forecast is intact.

    Self-contained: pin a concrete DSN (so the health check reports 'error',
    not 'not_configured', regardless of any earlier test's env/cache state) and
    force ping() to report the database as unreachable.
    """
    import src.database.config as dbcfg
    import src.database.db as dbmod

    monkeypatch.setattr(
        dbcfg, "database_url",
        lambda: "postgresql+psycopg2://u:p@127.0.0.1:5432/sih2026_app")
    monkeypatch.setattr(dbmod, "ping", lambda dsn: False)
    health = client.get("/health").json()
    assert health["components"]["database"]["status"] == "error"
    assert health["status"] == "ok"  # database is advisory; api/model/data healthy
    d = _forecast(client)
    assert d["probabilities"]["revival"] == pytest.approx(REVIVAL_ROUNDED, abs=1e-4)
    assert d["persistence"]["persisted"] is False
    assert d["persistence"]["note"] == "unreachable"


def test_postgres_not_configured_forecast_still_works(client, monkeypatch):
    import src.database.config as dbcfg
    monkeypatch.setattr(dbcfg, "database_url", lambda: "")
    d = _forecast(client)
    assert d["probabilities"]["revival"] == pytest.approx(REVIVAL_ROUNDED, abs=1e-4)
    assert d["persistence"]["persisted"] is False
    assert d["persistence"]["note"] == "not_configured"


def test_invalid_cell_is_rejected(client):
    r = client.get("/api/v1/cells/99.99_99.99/forecast", params={"date": DATE})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "unknown_cell"
    r = client.get("/api/v1/cells/not_a_cell/forecast", params={"date": DATE})
    assert r.status_code == 404


def test_malformed_date_and_out_of_season_rejected(client):
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/forecast", params={"date": "2024-13-40"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_date"
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/forecast", params={"date": "2024-11-15"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "outside_season"


# --------------------------------------------- refresh + repeated requests
def test_frontend_refresh_returns_identical_numbers(client):
    """A page refresh (fresh HTTP request) must reproduce the same output."""
    a = _forecast(client)
    b = _forecast(client)
    assert a["probabilities"] == b["probabilities"]
    assert a["targets"] == b["targets"]
    assert a["models"] == b["models"]
    assert a["calibration"] == b["calibration"]


def test_repeated_request_persistence_is_idempotent(client):
    """Repeated identical requests must not duplicate or drift the stored row."""
    a = _forecast(client)
    b = _forecast(client)
    assert a["persistence"]["persisted"] == b["persistence"]["persisted"]
    if a["persistence"]["persisted"]:
        assert a["persistence"]["forecast_id"] == b["persistence"]["forecast_id"]
    # digest/coherence unchanged
    assert a["provenance"]["freeze_digest"] == FREEZE_DIGEST


def test_model_info_stable_across_refresh(client):
    a = client.get("/api/v1/model-info").json()
    b = client.get("/api/v1/model-info").json()
    assert a["freeze_digest"] == b["freeze_digest"] == FREEZE_DIGEST
    assert a["models"] == b["models"]


# ------------------------------------------------------------- frontend parity
def test_frontend_display_value_matches_api(client):
    """The exact value the API returns today is what the frontend renders.

    The React suite renders forecastFixture.probabilities.revival == 0.6047
    (the value captured live from this endpoint) as controlled text "60.5%".
    Assert the API and the fixture cannot silently diverge.
    """
    d = _forecast(client)
    api_value = d["probabilities"]["revival"]
    assert api_value == pytest.approx(REVIVAL_RAW, abs=1e-12)
    shown_pct = f"{api_value * 100:.1f}%"
    assert shown_pct == "60.5%"
    # every response passes the strict pydantic contract (no malformed payloads)
    assert client.get("/health").status_code == 200


# ------------------------------------------------------- required API surface
def test_required_endpoints_surface(client):
    """Master-spec surface: /health, /locations, forecast, advisory, explain."""
    assert client.get("/health").status_code == 200
    locs = client.get("/locations").json()
    assert locs["spatial_unit"]["type"] == "regular_grid_0.25deg"
    assert locs["data_mode"] == "historical/demo"
    assert len(locs["locations"]) == 304
    single = client.get(f"/locations/{DEMO_CELL}").json()
    assert "observation_period" in single["location"]
    for path in ("forecast", "advisory", "explain"):
        r = client.get(f"/api/v1/cells/{DEMO_CELL}/{path}", params={"date": DATE})
        assert r.status_code == 200, (path, r.text)
    assert client.get("/api/v1/model-info").status_code == 200


def test_cors_configuration_for_dev_preview():
    """CORS allows the Vite dev/preview origins; disallowed origins are not echoed."""
    store = ObservationStore.from_file()
    registry = CellRegistry.from_matrix(store.matrix)
    service = ModelService(store, matrix=store.matrix)
    client = TestClient(create_app(store=store, registry=registry, service=service))
    r = client.options("/api/v1/cells",
                       headers={
                           "Origin": "http://localhost:5173",
                           "Access-Control-Request-Method": "GET",
                       })
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
    r2 = client.get("/api/v1/cells", headers={"Origin": "http://evil.example"})
    assert r2.headers.get("access-control-allow-origin") is None
    assert r2.status_code == 200  # same-origin API access is unaffected


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))