"""Demo geography endpoints + decision/advisory API (offline, frozen matrix).

Validates that the demo hierarchy resolves to REAL pilot cells, answers the
decision/village-advisory/deliver/scenario endpoints, and never fabricates a
probability. Uses the same TestClient construction as test_mvp_api.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.serving.api import create_app  # noqa: E402
from src.serving.models import ModelService  # noqa: E402
from src.serving.registry import CellRegistry  # noqa: E402
from src.serving.store import ObservationStore  # noqa: E402


@pytest.fixture(scope="module")
def client():
    store = ObservationStore.from_file()
    registry = CellRegistry.from_matrix(store.matrix)
    service = ModelService(store, matrix=store.matrix)
    app = create_app(store=store, registry=registry, service=service)
    return TestClient(app)


def test_geography_demo_serves_hierarchy(client):
    r = client.get("/api/v1/geography/demo")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "demo/simulated"
    assert "note" in body and "NOT authoritative" in body["note"]
    assert body["pilot_cell_count"] == 304
    st = body["hierarchy"][0]
    assert st["state"]["name"] == "Tamil Nadu"
    dist = st["districts"][0]
    assert dist["district"]["name"] == "Thanjavur"
    blk = dist["blocks"][0]
    assert blk["block"]["name"] == "Orathanadu"
    cells = {v["cell_id"] for v in blk["villages"]}
    assert cells and all(c in {c["cell_id"] for c in client.get("/api/v1/cells").json()["cells"]}
                         for c in cells)


def test_geography_demo_resolve_village(client):
    r = client.get("/api/v1/geography/demo/TN-ORA-001")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "demo/simulated"
    assert body["cell_id"] == "10.75_77.5"
    assert body["village"]["name"] == "Demo Agricultural Village"
    assert body["block"]["name"] == "Orathanadu"


def test_geography_demo_unknown_village_404(client):
    r = client.get("/api/v1/geography/demo/TN-NOPE-9")
    assert r.status_code == 404


def test_decision_endpoint_returns_composite_decision(client):
    r = client.get("/api/v1/cells/10.75_77.5/decision?date=2024-06-07")
    assert r.status_code == 200
    d = r.json()["decision"]
    assert d["decision"] in ("SOW", "WAIT", "MONITOR", "PREPARE", "IRRIGATION_PREPARE")
    assert d["false_onset_risk"] in ("low", "medium", "high")
    assert d["critical_reasons"] and d["thresholds_version"]


def test_village_advisory_endpoint_is_bilingual(client):
    r = client.get(
        "/api/v1/cells/10.75_77.5/village-advisory?date=2024-06-07&crop=paddy"
        "&village_name=Demo+Village&village_id=TN-ORA-001")
    assert r.status_code == 200
    msgs = r.json()["advisory"]["messages"]
    assert "VILLAGE:" in msgs["en"]["print_head"]
    assert ord(msgs["ta"]["block"][0]) > 0x0B80, "Tamil block present (Unicode Tamil)"


def test_deliver_endpoint_mocks_and_traceable(client):
    for channel in ("notice_print", "ivr", "sms"):
        r = client.get(f"/api/v1/cells/10.75_77.5/deliver?date=2024-06-07&channel={channel}")
        assert r.status_code == 200
        body = r.json()
        assert body["delivery"]["channel"] == channel
        assert "MOCK" in body["delivery"]["via"] or "MOCK" in body["delivery"]["mock_notice"]
    bad = client.get("/api/v1/cells/10.75_77.5/deliver?channel=esp")
    assert bad.status_code == 422


def test_demo_scenarios_are_computed_not_fabricated(client):
    r = client.get("/api/v1/demo/scenarios")
    assert r.status_code == 200
    sc = r.json()["scenarios"]
    assert len(sc) >= 3
    for s in sc:
        assert "probabilities" not in s["decision"]  # decision only, inputs provenance elsewhere
        assert s["decision"]["decision"] in (
            "SOW", "WAIT", "MONITOR", "PREPARE", "IRRIGATION_PREPARE")
    # the false-onset day must produce WAIT (honest derived signal)
    day0607 = next(s for s in sc if s["forecast_date"] == "2024-06-07")
    assert day0607["decision"]["decision"] == "WAIT"


def test_cells_risk_serves_whole_grid(client):
    r = client.get("/api/v1/demo/cells-risk?date=2024-08-12")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] in ("historical", "demo/simulated")
    assert body["data_mode"] == "historical/demo"
    assert str(body["forecast_date"]) == "2024-08-12"
    assert body["n_cells"] > 10
    levels = {c["risk_level"] for c in body["cells"]}
    assert levels <= {"low", "moderate", "high", "critical"}
    for c in body["cells"]:
        for field in ("cell_id", "lat", "lon", "region", "risk_level", "hazard_p",
                      "dominant_hazard", "decision", "false_onset_risk",
                      "monsoon_status", "rain_t_mm", "dry_streak_days"):
            assert field in c, f"cells field missing: {field}"
        assert 0.0 <= c["hazard_p"] <= 1.0
        assert c["decision"] in ("SOW", "WAIT", "MONITOR", "PREPARE",
                                 "IRRIGATION_PREPARE")
    assert body["legend"][0]["level"] == "low" and body["legend"][3]["level"] == "critical"


def test_cells_risk_not_fabricated_and_reproducible(client):
    a = client.get("/api/v1/demo/cells-risk?date=2024-08-12").json()["cells"]
    b = client.get("/api/v1/demo/cells-risk?date=2024-08-12").json()["cells"]
    assert a == b, "same date must give identical (deterministic) risk index"
    c1 = next(c for c in a if c["cell_id"] == "10.75_77.5")
    assert 0.0 <= c1["probabilities"]["dry_spell"] <= 1.0
    assert 0.0 <= c1["probabilities"]["revival"] <= 1.0


def test_cells_risk_defaults_and_bad_date(client):
    r = client.get("/api/v1/demo/cells-risk")
    assert r.status_code == 200
    assert r.json()["n_cells"] > 0
    bad = client.get("/api/v1/demo/cells-risk?date=2020-05-01")
    assert bad.status_code == 422