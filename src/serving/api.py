"""FastAPI backend for the MVP (contract: reports/MVP_API_CONTRACT.md).

Endpoints
- GET /health
- GET /locations
- GET /locations/{cell_id}
- GET /api/v1/cells/{cell_id}/forecast?date=YYYY-MM-DD
- GET /api/v1/cells/{cell_id}/advisory?date=YYYY-MM-DD
- GET /api/v1/cells/{cell_id}/explain?date=YYYY-MM-DD

Static frontend is mounted at "/".

Serving is historical/demo mode: values are computed by the FROZEN models on demand
from the frozen Phase H feature matrix - never hardcoded.
"""
from __future__ import annotations

from datetime import date as date_cls
from datetime import datetime, timezone

import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from src.serving import config as C
from src.serving.models import ModelService
from src.serving.registry import CellRegistry
from src.serving.rules import (BANDS, EXPLAIN_CAVEAT, band_of, band_meaning,
                               build_cards_with_bands)
from src.serving.schemas import CellsResponse, HealthResponse
from src.serving.store import ObservationStore, in_jjas

APP_NAME = "SIH26086 Monsoon Decision Support"
MODEL_VERSION = "FREEZE_H"


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


def _card(comps: ServingComponents, pred: dict, target: str) -> dict:
    c = dict(pred[target])
    p = c["probability"]
    c["band"] = band_of(p)
    c["band_meaning"] = band_meaning(band_of(p))
    c["calibration_ece_val"] = comps.service.freeze["targets"][target]["validation_ece"]
    c["probability_pct"] = round(float(p) * 100, 1)
    return c


def create_app(store=None, registry=None, service=None) -> FastAPI:
    app = FastAPI(title=APP_NAME, version=MODEL_VERSION, docs_url="/docs")

    if store is not None and registry is not None and service is not None:
        app.state.components = ServingComponents(store, registry, service)

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
        if model["status"] != "ok" or data["status"] != "ok" or db["status"] == "error":
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
                           "database": db},
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

    @app.get("/api/v1/cells/{cell_id}/forecast")
    def forecast(cell_id: str, request: Request,
                 date: str | None = Query(default=None, description="YYYY-MM-DD")):
        comps = _components(request)
        cell = _resolve_cell(comps.registry, cell_id)
        ts = _parse_date(date, comps.store, cell_id)
        row = comps.store.row(cell_id, ts)
        _check_data(comps, row, cell_id, ts)
        pred = comps.service.predict(cell_id, ts)
        targets = {t: _card(comps, pred, t) for t in C.TARGETS}
        return {
            "cell_id": cell_id,
            "lat": cell["lat"], "lon": cell["lon"],
            "region": cell["region"],
            "forecast_date": str(ts.date()),
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "data_mode": C.DATA_MODE,
            "spatial_unit": C.SPATIAL_UNIT,
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