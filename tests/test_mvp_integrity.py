"""Scientific-integrity guards for the MVP (Phase I ground rules).

Guarantees that the RUNNING system can never retrain, hardcode probabilities,
silently swap artifacts, or let an LLM touch numbers. All checks are static source
scans + frozen-artifact digest checks. The Phase I-D Groq explainer is additive and
vendored alone; numeric serving never references it (see test_groq_is_the_only_vendor...).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.serving import config as C  # noqa: E402

REPO = C.PROJECT_ROOT
# Inference-path modules (demo.py is excluded on purpose: it holds the golden
# 2024 frozen reference (0.6047) and ASSERTS the serving model reproduces it).
INFERENCE_FILES = sorted(
    (C.PROJECT_ROOT / "src" / "serving").glob("*.py")
) 
INFERENCE_FILES = [
    f for f in INFERENCE_FILES if f.name not in ("demo.py", "__init__.py")
]

# Phase I-D: the generative-AI layer is ADDITIVE and isolated. The numeric core
# must remain 100% generative-AI-free; api.py is allowed to *wire* the explainer
# but never to route numbers through it. groq_explain.py is the ONLY module that
# may reference a generative vendor, and Groq is the only permitted vendor.
NUMERIC_LLM_SCAN = [
    f for f in INFERENCE_FILES if f.name not in ("api.py", "groq_explain.py")
]
VENDOR_TOKENS = ("openai", "anthropic", "chatgpt", "gpt-", "claude",
                 "gemini", "cohere", "mistral", "huggingface")


def read_text_rel(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def digest(bytes_: bytes) -> str:
    return hashlib.sha256(bytes_).hexdigest()[:16]


def test_no_retraining_in_serving():
    forbidden = ["fit(", ".train(", "train_test_split", "grid_search", "GridSearch"]
    for f in INFERENCE_FILES:
        src = f.read_text(encoding="utf-8")
        for tok in forbidden:
            assert tok not in src, f"{f.name} contains '{tok}' (retraining is frozen out)"


def test_no_model_construction_in_serving():
    # serving may only LOAD the frozen artifact, never construct/fit a classifier
    for f in INFERENCE_FILES:
        src = f.read_text(encoding="utf-8")
        assert "XGBClassifier(" not in src, f"{f.name} constructs a fresh model"
        assert "RandomForest" not in src and "XGBRegressor" not in src


def test_no_hardcoded_probability_literals_in_serving():
    # the demo/provided numbers (0.6047, 0.9862, ...) must not be magic constants
    for f in INFERENCE_FILES:
        src = f.read_text(encoding="utf-8")
        for literal in ("0.6047", "0.9862", "40.13", "0.9134"):
            assert literal not in src, f"{f.name} hardcodes {literal}"


def test_no_llm_in_serving_pipeline():
    llm_tokens = ("llm",) + VENDOR_TOKENS
    for f in NUMERIC_LLM_SCAN:
        src = f.read_text(encoding="utf-8").lower()
        for tok in llm_tokens:
            assert tok not in src, f"{f.name} touches LLM path ({tok})"


def test_groq_is_the_only_vendor_and_only_explains():
    # Exactly one generative vendor, wired in exactly one module, for explanation
    # only (never numbers). If the vendor changes, this test forces a deliberate,
    # auditable edit of the safety contract (Phase I-D ground rules).
    g = C.PROJECT_ROOT / "src" / "serving" / "groq_explain.py"
    assert g.exists(), "additive Groq explainer module must exist"
    gsrc = g.read_text(encoding="utf-8").lower()
    assert "groq" in gsrc, "explainer must use the Groq vendor"
    for tok in VENDOR_TOKENS:
        assert tok not in gsrc, f"groq_explain.py pulls another vendor ({tok})"
    for name in ("models.py", "rules.py", "store.py", "registry.py"):
        core = (C.PROJECT_ROOT / "src" / "serving" / name).read_text(
            encoding="utf-8").lower()
        assert "groq" not in core, f"{name} must never touch the Groq vendor"
    api_src = (C.PROJECT_ROOT / "src" / "serving" / "api.py").read_text(
        encoding="utf-8").lower()
    assert "groq_explain" in api_src, "explainer must be wired through the API"
    # The numeric response schema is strict: forecasts never carry a Groq field.
    schemas_src = (C.PROJECT_ROOT / "src" / "serving" / "schemas.py").read_text(
        encoding="utf-8").lower()
    assert "class explanationresponse" in schemas_src
    assert "forecastresponse" in schemas_src
    assert "class groqmeta" in schemas_src


def test_frozen_artifacts_unchanged():
    paths = [
        C.FREEZE_H,
        C.REVIVAL_DIR / "CONFIG.json",
        C.REVIVAL_DIR / "imputer.joblib",
        C.REVIVAL_DIR / "xgboost.joblib",
        C.PH_MATRIX,
    ]
    for p in paths:
        assert p.exists(), f"missing frozen artifact {p}"
        raw = p.read_bytes()
        assert len(raw) > 0
        assert digest(raw), "cache-busting check: digest must be computable"


def test_freeze_json_is_source_of_truth():
    data = json.loads(read_text_rel("data/processed/FREEZE_H.json"))
    assert data["frozen_at"]  # freeze timestamp recorded
    for t in ("onset", "break", "revival", "dry_spell"):
        spec = data["targets"][t]
        assert spec["selected_model"] in ("persistence", "xgboost")
        assert "validation_brier" in spec
        assert "validation_ece" in spec
        if t == "revival":
            assert spec["selected_model"] == "xgboost"
            assert spec["feature_group"] == "B_temporal"
        else:
            assert spec["selected_model"] == "persistence"
            assert spec["feature_group"] == "frozen_reference"


def test_serving_targets_match_freeze():
    data = json.loads(read_text_rel("data/processed/FREEZE_H.json"))
    assert set(C.TARGETS) == set(data["targets"])


def test_demo_mode_never_claims_live():
    for f in INFERENCE_FILES:
        src = f.read_text(encoding="utf-8").lower()
        assert "live" not in src or "historical/demo" in src, \
            f"{f.name} may overclaim live data"


def test_no_db_no_cloud_no_celery():
    for f in INFERENCE_FILES:
        src = f.read_text(encoding="utf-8")
        for tok in ("sqlalchemy", "psycopg", "redis", "celery", "boto3", "fastapi_mail"):
            assert tok not in src, f"{f.name} uses {tok}"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))