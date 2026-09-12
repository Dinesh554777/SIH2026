"""Phase I-A backend foundation endpoint tests: /health, /api/v1/cells, /docs."""
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


def test_health_reports_all_components(client):
    r = client.get("/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "ok"
    comp = d["components"]
    assert comp["api"]["status"] == "ok"
    assert comp["model"]["status"] == "ok"
    assert comp["model"]["freeze_digest"]
    assert comp["data"]["status"] == "ok"
    assert comp["data"]["n_cells"] == 304
    assert comp["database"]["dsn_set"] is False or comp["database"]["status"] != "not_configured"
    # never fake a connected database when the DSN is absent
    if not comp["database"]["dsn_set"]:
        assert comp["database"]["status"] == "not_configured"


def test_cells_endpoint_returns_304(client):
    r = client.get("/api/v1/cells")
    assert r.status_code == 200
    d = r.json()
    assert d["count"] == 304
    assert len(d["cells"]) == 304
    first = d["cells"][0]
    assert {"cell_id", "lat", "lon", "region", "admin_note"} <= set(first)
    assert {c["region"] for c in d["cells"]} == {"TN", "MH", "KA"}


def test_cells_endpoint_same_registry_as_locations(client):
    cells = client.get("/api/v1/cells").json()["cells"]
    locs = client.get("/locations").json()["locations"]
    assert [c["cell_id"] for c in cells] == [l["cell_id"] for l in locs]


def test_cells_method_not_allowed(client):
    r = client.post("/api/v1/cells")
    assert r.status_code == 405


def test_docs_served(client):
    r = client.get("/docs")
    assert r.status_code == 200
    assert "swagger" in r.text.lower()


def test_legacy_docs_redirects(client):
    r = client.get("/api/docs", follow_redirects=False)
    assert r.status_code in (301, 302, 307, 308)
    assert r.headers["location"] == "/docs"


def test_unknown_route_404(client):
    r = client.get("/api/v1/does-not-exist")
    assert r.status_code == 404


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))