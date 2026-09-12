"""FastAPI backend for the MVP (contract: reports/MVP_API_CONTRACT.md).

Endpoints
- GET /health
- GET /locations
- GET /locations/{cell_id}
- GET /api/v1/cells
- GET /api/v1/cells/{cell_id}/forecast?date=YYYY-MM-DD
- GET /api/v1/cells/{cell_id}/advisory?date=YYYY-MM-DD
- GET /api/v1/cells/{cell_id}/explain?date=YYYY-MM-DD
- GET /api/v1/model-info

Static frontend is mounted at "/".

Serving is historical/demo mode: values are computed by the FROZEN models on demand
from the frozen Phase H feature matrix - never hardcoded. The API never labels
historical data as live; `mode` is "historical" until a live feed exists.
"""
from __future__ import annotations

import os
import re
from datetime import date as date_cls
from datetime import datetime, timezone

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.serving import config as C
from src.serving.groq_explain import (GroqExplainer, build_explanation_input,
                                      explain_block)
from src.serving.models import ModelService
from src.serving.registry import CellRegistry
from src.serving.rules import (BANDS, EXPLAIN_CAVEAT, band_of, band_meaning,
                               build_cards_with_bands)
from src.serving.schemas import (CellsResponse, ExplanationResponse,
                                 ForecastResponse, HealthResponse,
                                 ModelInfoResponse)
from src.serving.store import ObservationStore, in_jjas

APP_NAME = "SIH26086 Monsoon Decision Support"
MODEL_VERSION = "FREEZE_H"

# Frontend dev/preview origins allowed to call the API directly. Override with
# CORS_ORIGINS (comma-separated) in .env for LAN/demo use. No credentials/cookies
# are used, so allow_credentials stays False.
DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:4173", "http://127.0.0.1:4173",
]


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "")
    if raw.strip():
        return [o.strip() for o in raw.split(",") if o.strip()]
    return list(DEFAULT_CORS_ORIGINS)


class ServingComponents:
    def __init__(self, store: ObservationStore, registry: CellRegistry, service: ModelService):
        self.store = store
        self.registry = registry
        self.service = service


def _build_default_components() -> ServingComponents:
    store = ObservationStore.from_file()
    registry = CellRegistry.from_matrix(store.matrix)
    service = ModelService(store, matrix=store.matrix)
    return ServingComponents(store, registry, service)


def _components(request: Request) -> ServingComponents:
    comps = getattr(request.app.state, "components", None)
    if comps is None:
        comps = _build_default_components()
        request.app.state.components = comps
    return comps


def _error(status: int, code: str, message: str, detail: str | None = None) -> HTTPException:
    return HTTPException(status_code=status,
                         detail={"error": {"code": code, "message": message,
                                           "detail": detail}})


def _mode() -> str:
    """Historical vs live. No live feed exists, so this is always historical."""
    return "live" if C.DATA_MODE == "live" else "historical"


def _explainer(request: Request) -> GroqExplainer:
    """Return the injected explainer (tests) or a default env-based one."""
    injected = getattr(request.app.state, "groq", None)
    return injected if isinstance(injected, GroqExplainer) else GroqExplainer()


def _lang_ok(lang: str) -> bool:
    return bool(re.match(r"^[a-zA-Z]{2}(?:-[A-Za-z]{2,8})?$", lang))


def _parse_date(value: str | None, store: ObservationStore, cell_id: str) -> pd.Timestamp:
    if value is None or value == "":
        return store.latest_date(cell_id)
    try:
        ts = pd.Timestamp(date_cls.fromisoformat(value))
    except ValueError:
        raise _error(422, "invalid_date",
                     f"Invalid date '{value}'. Use YYYY-MM-DD.")
    if not in_jjas(ts):
        raise _error(422, "outside_season",
                     "Forecasts are defined only for the JJAS monsoon season (Jun 1 - Sep 30).")
    return ts


def _resolve_cell(registry: CellRegistry, cell_id: str) -> dict:
    if not registry.is_valid_id(cell_id):
        raise _error(404, "unknown_cell", f"Unknown cell id '{cell_id}'.")
    cell = registry.get(cell_id)
    if cell is None:
        raise _error(404, "unknown_cell", f"Unknown cell id '{cell_id}'.")
    return cell


def _check_data(comps: ServingComponents, row, cell_id: str, date: pd.Timestamp) -> None:
    if row is None:
        raise _error(404, "date_not_available",
                     f"No observations for cell {cell_id} on {date.date()}.")
    completeness = comps.store.data_completeness(row, comps.service.revival_features)
    if completeness < 0.9:
        raise _error(409, "insufficient_data",
                     f"Insufficient observations for cell {cell_id} on {date.date()} "
                     f"(completeness={completeness:.0%}).")


def _band_list() -> list[dict]:
    return [{"band": b[0], "range": [b[1], round(b[2], 4)], "meaning": b[3]} for b in BANDS]


def _database_status() -> dict:
    """Honest database health. Never pretends: reports not_configured when no DSN."""
    from src.database.config import database_url as resolve_db_url
    from src.database.db import ping

    dsn = resolve_db_url()
    if not dsn:
        return {"status": "not_configured", "dsn_set": False}
    if ping(dsn):
        return {"status": "ok", "dsn_set": True}
    return {"status": "error", "dsn_set": True,
            "detail": "DATABASE_URL is set but the database is unreachable."}


def _persist_forecast(comps: ServingComponents, cell_id: str, ts: pd.Timestamp,
                      pred: dict) -> dict:
    """Optionally persist the forecast + advisories into PostgreSQL.

    Persistence is best-effort: the forecast endpoint never fails because the
    database is down. `mode` is recorded as historical/demo (no live feed).
    """
    from src.database.config import database_url as resolve_db_url
    from src.database.db import connect, ping
    from src.database.repository import store_forecast_bundle

    dsn = resolve_db_url()
    base = {"database": "postgresql", "mode": "historical"}
    if not dsn:
        return {**base, "persisted": False, "note": "not_configured"}
    if not ping(dsn):
        return {**base, "persisted": False, "note": "unreachable"}
    try:
        bundle = build_cards_with_bands(comps.service, cell_id, ts, pred)
        probabilities = {t: float(pred[t]["probability"]) for t in C.TARGETS}
        with connect() as session:
            fid = store_forecast_bundle(
                session, cell_id=cell_id, forecast_date=ts,
                probabilities=probabilities,
                model_version=comps.service.freeze_digest,
                mode="historical/demo", bundle=bundle)
        return {**base, "persisted": True, "forecast_id": fid,
                "note": f"inserted into sih2026_app (digest {comps.service.freeze_digest})"}
    except Exception as exc:  # pragma: no cover - DB layer problems must never 500 the API
        return {**base, "persisted": False,
                "note": f"error: {type(exc).__name__}: {str(exc)[:180]}"}


def _card(comps: ServingComponents, pred: dict, target: str) -> dict:
    c = dict(pred[target])
    p = c["probability"]
    c["band"] = band_of(p)
    c["band_meaning"] = band_meaning(band_of(p))
    c["calibration_ece_val"] = comps.service.freeze["targets"][target]["validation_ece"]
    c["probability_pct"] = round(float(p) * 100, 1)
    return c


def _groq_status(request: Request) -> dict:
    """Honest Groq component. Booleans only - the API key is never returned."""
    ex = _explainer(request)
    return {"status": "ok" if ex.available else "not_configured",
            "key_set": ex.available,
            "model": ex.model if ex.available else None}


def create_app(store=None, registry=None, service=None, groq=None) -> FastAPI:
    app = FastAPI(title=APP_NAME, version=MODEL_VERSION, docs_url="/docs")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    if store is not None and registry is not None and service is not None:
        app.state.components = ServingComponents(store, registry, service)
    if groq is not None:
        app.state.groq = groq

    @app.exception_handler(HTTPException)
    async def _http_exc_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    @app.get("/api/docs", include_in_schema=False)
    def legacy_docs_redirect():
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/docs")

    @app.get("/health", response_model=HealthResponse)
    def health(request: Request):
        db = _database_status()
        comps = None
        load_error = None
        try:
            comps = _components(request)
        except Exception as exc:  # honest degraded state, not a fake "ok"
            load_error = f"{type(exc).__name__}: {exc}"[:300]

        if comps is None:
            model = {"status": "error", "detail": load_error}
            data = {"status": "error", "detail": load_error}
        else:
            n_cells = len(comps.registry.ids)
            lo, hi = comps.store.date_range(comps.registry.ids[0])
            model = {"status": "ok", "model_version": MODEL_VERSION,
                     "freeze_digest": comps.service.freeze_digest,
                     "selected_models": C.MODEL_SPEC}
            data = {"status": "ok", "matrix": str(C.PH_MATRIX), "n_cells": n_cells,
                    "observation_period": {"start": str(lo.date()), "end": str(hi.date())}}

        overall = "ok"
        # The PostgreSQL persistence layer is best-effort (Phase I-C): a down
        # database does NOT degrade serving. Its honest state is in components.
        if model["status"] != "ok" or data["status"] != "ok":
            overall = "degraded"

        return {
            "status": overall,
            "app": APP_NAME,
            "model_version": MODEL_VERSION,
            "data_mode": C.DATA_MODE,
            "freeze": str(C.FREEZE_H),
            "freeze_digest": comps.service.freeze_digest if comps else None,
            "spatial_unit": C.SPATIAL_UNIT,
            "as_of": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "components": {"api": {"status": "ok"}, "model": model, "data": data,
                           "database": db, "groq": _groq_status(request)},
        }

    @app.get("/api/v1/cells", response_model=CellsResponse)
    def cells_list(request: Request):
        comps = _components(request)
        items = [comps.registry.get(c) for c in comps.registry.ids]
        return {
            "count": len(items),
            "cells": items,
            "spatial_unit": C.SPATIAL_UNIT,
            "data_mode": C.DATA_MODE,
            "forecast_horizon_note": C.FORECAST_HORIZON_NOTE,
        }

    @app.get("/locations")
    def locations(request: Request):
        comps = _components(request)
        return {"locations": [comps.registry.get(c) for c in comps.registry.ids],
                "spatial_unit": C.SPATIAL_UNIT,
                "data_mode": C.DATA_MODE,
                "forecast_horizon_note": C.FORECAST_HORIZON_NOTE}

    @app.get("/locations/{cell_id}")
    def location(cell_id: str, request: Request):
        comps = _components(request)
        cell = _resolve_cell(comps.registry, cell_id)
        lo, hi = comps.store.date_range(cell_id)
        cell = dict(cell)
        cell["observation_period"] = {"start": str(lo.date()), "end": str(hi.date())}
        return {"location": cell, "data_mode": C.DATA_MODE}

    @app.get("/api/v1/cells/{cell_id}/forecast", response_model=ForecastResponse)
    def forecast(cell_id: str, request: Request,
                 date: str | None = Query(default=None, description="YYYY-MM-DD")):
        comps = _components(request)
        cell = _resolve_cell(comps.registry, cell_id)
        ts = _parse_date(date, comps.store, cell_id)
        row = comps.store.row(cell_id, ts)
        _check_data(comps, row, cell_id, ts)
        pred = comps.service.predict(cell_id, ts)
        targets = {t: _card(comps, pred, t) for t in C.TARGETS}
        data_mode = C.DATA_MODE
        forecast_mode = _mode()
        probabilities = {t: float(pred[t]["probability"]) for t in C.TARGETS}
        fingerprint = lambda t: {k: pred[t][k] for k in ("model", "feature_group")
                                 if k in pred[t]}
        return {
            "cell_id": cell_id,
            "lat": cell["lat"], "lon": cell["lon"],
            "region": cell["region"],
            "forecast_date": str(ts.date()),
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mode": forecast_mode,
            "data_mode": data_mode,
            "spatial_unit": C.SPATIAL_UNIT,
            "probabilities": probabilities,
            "models": {t: dict(fingerprint(t),
                               n_features=pred[t]["n_features"]) if "n_features" in pred[t]
                       else fingerprint(t) for t in C.TARGETS},
            "calibration": {
                t: {"ece": comps.service.freeze["targets"][t]["validation_ece"],
                    "brier": comps.service.freeze["targets"][t]["validation_brier"]}
                for t in C.TARGETS
            },
            "observations_used": comps.service.observations_used(row),
            "targets": targets,
            "confidence": {
                "note": "Probability is a calibrated model output, not a guarantee. "
                        "Bands are communication aids.",
                "bands": _band_list(),
                "calibration": [
                    {
                        "state": t,
                        "ece": comps.service.freeze["targets"][t]["validation_ece"],
                        "brier": comps.service.freeze["targets"][t]["validation_brier"],
                        "period": "2022-2023",
                    }
                    for t in C.TARGETS
                ],
            },
            "provenance": comps.service.provenance(),
            "persistence": _persist_forecast(comps, cell_id, ts, pred),
        }

    @app.get("/api/v1/cells/{cell_id}/advisory")
    def advisory(cell_id: str, request: Request,
                 date: str | None = Query(default=None, description="YYYY-MM-DD")):
        comps = _components(request)
        cell = _resolve_cell(comps.registry, cell_id)
        ts = _parse_date(date, comps.store, cell_id)
        row = comps.store.row(cell_id, ts)
        _check_data(comps, row, cell_id, ts)
        pred = comps.service.predict(cell_id, ts)
        bundle = build_cards_with_bands(comps.service, cell_id, ts, pred)
        dom = bundle["dominant"]
        dom_card = next(c for c in bundle["cards"] if c["state"] == dom)
        summary = (f"{dom_card['state_label']} probability is {dom_card['probability_pct']:.0f}% "
                   f"({dom_card['band']}). {dom_card['interpretation']}")
        return {
            "cell_id": cell_id,
            "lat": cell["lat"], "lon": cell["lon"],
            "region": cell["region"],
            "forecast_date": str(ts.date()),
            "data_mode": C.DATA_MODE,
            "summary": summary,
            "dominant_state": dom,
            "items": bundle["cards"],
            "current_signal": bundle["current_signal"],
            "evidence": bundle["evidence"],
            "disclaimer": bundle["disclaimer"],
            "provenance": comps.service.provenance(),
        }

    @app.get("/api/v1/cells/{cell_id}/explain")
    def explain(cell_id: str, request: Request,
                date: str | None = Query(default=None, description="YYYY-MM-DD")):
        comps = _components(request)
        cell = _resolve_cell(comps.registry, cell_id)
        ts = _parse_date(date, comps.store, cell_id)
        row = comps.store.row(cell_id, ts)
        _check_data(comps, row, cell_id, ts)
        sens = comps.service.sensitivity(cell_id, ts)
        rev = comps.service.predict(cell_id, ts)["revival"]
        return {
            "cell_id": cell_id,
            "lat": cell["lat"], "lon": cell["lon"],
            "forecast_date": str(ts.date()),
            "target": "revival",
            "probability": rev["probability"],
            "model": rev["model"],
            "feature_group": rev["feature_group"],
            "n_features": rev["n_features"],
            "sensitivity": sens,
            "caveat": EXPLAIN_CAVEAT,
            "provenance": comps.service.provenance("revival"),
        }

    @app.get("/api/v1/cells/{cell_id}/explanation", response_model=ExplanationResponse)
    def explanation(cell_id: str, request: Request,
                    date: str | None = Query(default=None, description="YYYY-MM-DD"),
                    lang: str = Query(default="en", description="ISO-639-1 language code")):
        """Human-friendly explanation of the frozen-model forecast.

        Groq may rephrase what the deterministic rules already computed; it never
        computes/modifies probabilities, and when it is unavailable the endpoint
        returns the deterministic fallback advisory (the system keeps working).
        """
        if not _lang_ok(lang):
            raise _error(422, "unsupported_lang", f"Invalid language code '{lang}'.")
        comps = _components(request)
        cell = _resolve_cell(comps.registry, cell_id)
        ts = _parse_date(date, comps.store, cell_id)
        row = comps.store.row(cell_id, ts)
        _check_data(comps, row, cell_id, ts)
        pred = comps.service.predict(cell_id, ts)
        bundle = build_cards_with_bands(comps.service, cell_id, ts, pred)
        probs = {t: float(pred[t]["probability"]) for t in C.TARGETS}
        payload = build_explanation_input(
            cell_id, str(ts.date()), probs, bundle,
            comps.service.provenance(), MODEL_VERSION)
        ex = _explainer(request)
        block = explain_block(ex, payload, bundle, lang)
        return {
            "cell_id": cell_id,
            "lat": cell["lat"], "lon": cell["lon"],
            "region": cell["region"],
            "forecast_date": str(ts.date()),
            "mode": _mode(),
            "data_mode": C.DATA_MODE,
            "lang": lang,
            "source": block["source"],
            "groq": {"status": block["status"],
                     "model": ex.model if ex.available else None,
                     "note": block["note"]},
            "summary": block["summary"],
            "why": block["why"],
            "action": block["action"],
            "caution": block["caution"],
            "probabilities": {t: round(probs[t], 4) for t in C.TARGETS},
            "dominant_state": bundle["dominant"],
            "provenance": comps.service.provenance(),
        }

    @app.get("/api/v1/model-info", response_model=ModelInfoResponse)
    def model_info(request: Request):
        """Frozen model strategy + provenance for every target (Phase I-C).

        Documents which artifacts produced the probabilities so the output is
        reproducible. No inference happens here; nothing is retrained or tuned.
        """
        comps = _components(request)
        tf = comps.service.freeze["targets"]
        models: dict = {}
        calibration: dict = {}
        for t in C.TARGETS:
            models[t] = {
                "strategy": C.MODEL_SPEC[t],
                "selected_model": tf[t]["selected_model"],
                "feature_group": tf[t]["feature_group"],
            }
            if t == C.REVIVAL_TARGET:
                models[t]["model_config"] = {
                    k: tf[t]["hyperparameters"][k]
                    for k in ("n_estimators", "max_depth", "learning_rate", "seed")}
                models[t]["n_features"] = len(comps.service.revival_features)
                models[t]["artifact"] = str(C.REVIVAL_DIR)
            calibration[t] = {"ece": tf[t]["validation_ece"],
                              "brier": tf[t]["validation_brier"]}
        return {
            "app": APP_NAME,
            "model_version": MODEL_VERSION,
            "freeze_file": str(C.FREEZE_H),
            "freeze_digest": comps.service.freeze_digest,
            "data_mode": C.DATA_MODE,
            "mode": _mode(),
            "spatial_unit": C.SPATIAL_UNIT,
            "train_period": comps.service.freeze["train_period"],
            "validation_period": comps.service.freeze["validation_period"],
            "test_period": comps.service.freeze["test_period"],
            "models": models,
            "calibration": calibration,
            "note": comps.service.freeze["note"],
            "forecast_horizon_note": C.FORECAST_HORIZON_NOTE,
        }

    return app


def mount_frontend(app: FastAPI, frontend_dir: str | None = None) -> FastAPI:
    from pathlib import Path

    d = Path(frontend_dir) if frontend_dir else (C.PROJECT_ROOT / "frontend")
    if d.exists():
        app.mount("/", StaticFiles(directory=str(d), html=True), name="frontend")
    return app


def build_app() -> FastAPI:
    return mount_frontend(create_app())


app = build_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.serving.api:app", host="127.0.0.1", port=8000, reload=False)