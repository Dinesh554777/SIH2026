"""Phase I-D Groq explanation/advisory layer tests.

Groq is an ENHANCEMENT only: every scenario must keep the application working
through the deterministic fallback. Tests inject a fake Groq transport; no real
API key, network call, or model is used. The API key must never appear in any
response.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.serving.api import create_app  # noqa: E402
from src.serving.groq_explain import (GroqExplainer,  # noqa: E402
                                      build_explanation_input, fallback_explanation,
                                      parse_and_validate)
from src.serving.models import ModelService  # noqa: E402
from src.serving.registry import CellRegistry  # noqa: E402
from src.serving.rules import build_cards_with_bands  # noqa: E402
from src.serving.store import ObservationStore  # noqa: E402

DEMO_CELL = "10.75_77.5"
FAKE_KEY = "super-secret-key-do-not-leak"


class FakeChoice:
    def __init__(self, content: str):
        self.message = type("FakeMessage", (), {"content": content})()


class FakeResponse:
    def __init__(self, content: str):
        self.choices = [FakeChoice(content)]


class FakeCompletions:
    def __init__(self, content: str, error: Exception | None = None, calls=None):
        self.content = content
        self.error = error
        self.calls = calls if calls is not None else []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return FakeResponse(self.content)


class FakeGroq:
    def __init__(self, content: str, error: Exception | None = None, calls=None):
        self.chat = type("FakeChat", (), {
            "completions": FakeCompletions(content, error, calls)})()


def _app_with(explainer: GroqExplainer) -> TestClient:
    store = ObservationStore.from_file()
    registry = CellRegistry.from_matrix(store.matrix)
    service = ModelService(store, matrix=store.matrix)
    app = create_app(store=store, registry=registry, service=service, groq=explainer)
    return TestClient(app)


def _payload() -> dict:
    store = ObservationStore.from_file()
    service = ModelService(store, matrix=store.matrix)
    pred = service.predict(DEMO_CELL, __import__("pandas").Timestamp("2024-08-12"))
    bundle = build_cards_with_bands(service, DEMO_CELL, __import__("pandas").Timestamp("2024-08-12"), pred)
    probs = {t: float(pred[t]["probability"]) for t in ("onset", "break", "revival", "dry_spell")}
    return build_explanation_input(DEMO_CELL, "2024-08-12", probs, bundle,
                                   service.provenance(), "FREEZE_H"), bundle


VALID_JSON = json.dumps({
    "summary": "Dry spell and break probabilities are elevated for this cell.",
    "why": "Observed conditions show a low 7-day rainfall sum with a long dry streak.",
    "action": "Continue monitoring rainfall persistence before committing field operations.",
    "caution": "Model probabilities are not certainty."
})


# ---------------------------------------------------------- explainer (unit)
def test_valid_response_parses():
    out = parse_and_validate(VALID_JSON)
    assert set(out) == {"summary", "why", "action", "caution"}
    assert "not certainty" in out["caution"]


def test_malformed_json_raises():
    with pytest.raises(Exception):
        parse_and_validate("this is not json")


def test_missing_key_rejected():
    with pytest.raises(Exception):
        parse_and_validate(json.dumps({"summary": "x", "why": "y"}))


def test_certainty_phrase_rejected():
    bad = json.dumps({"summary": "rain will definitely occur tomorrow",
                      "why": "y", "action": "z", "caution": "c"})
    with pytest.raises(Exception):
        parse_and_validate(bad)


def test_build_input_is_structured_and_faithful():
    payload, _ = _payload()
    assert payload["cell_id"] == DEMO_CELL
    assert set(payload["probabilities"]) == {"onset", "break", "revival", "dry_spell"}
    assert 0 <= payload["probabilities"]["revival"] <= 1
    assert payload["deterministic_advisory"]["dominant_state"] in (
        "onset", "break", "revival", "dry_spell")
    assert "models" in payload["model_provenance"]
    assert payload["deterministic_advisory"]["cards"][0]["probability"] is not None


# ------------------------------------------------------------------- endpoint
def test_endpoint_missing_key_uses_fallback():
    client = _app_with(GroqExplainer(api_key=""))
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/explanation")
    assert r.status_code == 200
    d = r.json()
    assert d["source"] == "fallback"
    assert d["groq"]["status"] == "not_configured"
    assert all(k in d for k in ("summary", "why", "action", "caution"))
    assert d["mode"] == "historical"


def test_endpoint_valid_groq_response():
    fake = FakeGroq(VALID_JSON)
    ex = GroqExplainer(api_key=FAKE_KEY, model="fake-model", client=fake)
    client = _app_with(ex)
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/explanation")
    assert r.status_code == 200
    d = r.json()
    assert d["source"] == "groq"
    assert d["groq"]["status"] == "ok"
    assert "elevated" in d["summary"]
    assert d["groq"]["model"] == "fake-model"


def test_endpoint_malformed_reply_falls_back():
    fake = FakeGroq("not json at all")
    ex = GroqExplainer(api_key=FAKE_KEY, client=fake)
    client = _app_with(ex)
    d = client.get(f"/api/v1/cells/{DEMO_CELL}/explanation").json()
    assert d["source"] == "fallback"
    assert d["groq"]["status"] == "error"
    # fallback carries the deterministic summary (dominant state % + band)
    assert "probability is" in d["summary"]


def test_endpoint_api_timeout_falls_back():
    import groq
    error = groq.APITimeoutError("timed out")
    fake = FakeGroq("", error=error)
    ex = GroqExplainer(api_key=FAKE_KEY, client=fake)
    client = _app_with(ex)
    d = client.get(f"/api/v1/cells/{DEMO_CELL}/explanation").json()
    assert d["source"] == "fallback"
    assert d["groq"]["status"] == "error"


def test_endpoint_groq_unavailable_raises():
    import httpx
    import groq

    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    error = groq.APIStatusError("unavailable", response=httpx.Response(500, request=request),
                                body=None)
    fake = FakeGroq("", error=error)
    ex = GroqExplainer(api_key=FAKE_KEY, client=fake)
    client = _app_with(ex)
    d = client.get(f"/api/v1/cells/{DEMO_CELL}/explanation").json()
    assert d["source"] == "fallback"


def test_api_key_never_leaked():
    fake = FakeGroq(VALID_JSON)
    ex = GroqExplainer(api_key=FAKE_KEY, model="fake", client=fake)
    client = _app_with(ex)
    r = client.get("/health")
    assert FAKE_KEY not in r.text
    d = client.get(f"/api/v1/cells/{DEMO_CELL}/explanation").json()
    blob = json.dumps(d)
    assert FAKE_KEY not in blob
    mi = client.get("/api/v1/model-info")
    assert FAKE_KEY not in mi.text
    # health groq component exposes only a boolean + model name
    comp = r.json()["components"]["groq"]
    assert "key_set" in comp and comp["key_set"] is True
    assert comp["model"] == "fake"


def test_fallback_advisory_is_deterministic():
    _, bundle = _payload()
    a = fallback_explanation(bundle, "en")
    b = fallback_explanation(bundle, "en")
    assert a == b
    assert "suggested action" not in a["action"].lower()  # uses rules table verbatim


def test_endpoint_invalid_cell_404():
    client = _app_with(GroqExplainer(api_key=""))
    r = client.get("/api/v1/cells/99.99_99.99/explanation")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "unknown_cell"


def test_endpoint_invalid_lang_422():
    client = _app_with(GroqExplainer(api_key=""))
    r = client.get(f"/api/v1/cells/{DEMO_CELL}/explanation", params={"lang": "!!"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "unsupported_lang"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))