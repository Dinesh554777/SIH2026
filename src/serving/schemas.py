"""Pydantic response schemas for the FastAPI backend foundation (Phase I-A).

Endpoint payloads remain plain dicts on the wire (contract: reports/MVP_API_CONTRACT.md);
these models document the stable shape in /docs and validate the response at runtime.
Extra keys are allowed so future phases can extend responses without breaking the contract.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

_SCHEMA_CFG = ConfigDict(extra="allow", populate_by_name=True)


class ComponentStatus(BaseModel):
    """Base shape shared by the /health component checks."""

    model_config = _SCHEMA_CFG

    status: str = Field(description="ok | not_configured | error | not_loaded")


class ApiComponent(ComponentStatus):
    pass


class ModelComponent(ComponentStatus):
    model_version: str | None = None
    freeze_digest: str | None = None
    selected_models: dict[str, str] | None = None


class DataComponent(ComponentStatus):
    matrix: str | None = None
    n_cells: int | None = None
    observation_period: dict[str, str] | None = None


class DatabaseComponent(ComponentStatus):
    dsn_set: bool = False
    detail: str | None = None


class HealthResponse(BaseModel):
    """GET /health payload (extended contract, backward-compatible keys)."""

    model_config = _SCHEMA_CFG

    status: str = Field(description="ok | degraded")
    app: str
    model_version: str
    data_mode: str
    freeze: str | None = None
    freeze_digest: str | None = None
    spatial_unit: dict[str, Any] | None = None
    as_of: str
    components: dict[str, Any]


class CellEntry(BaseModel):
    """One pilot grid cell as returned by the cell-list endpoints."""

    model_config = _SCHEMA_CFG

    cell_id: str
    lat: float
    lon: float
    region: str
    admin_note: str = "grid_cell_only"


class CellsResponse(BaseModel):
    """GET /api/v1/cells payload."""

    model_config = _SCHEMA_CFG

    count: int
    cells: list[CellEntry]
    spatial_unit: dict[str, Any]
    data_mode: str
    forecast_horizon_note: str | None = None


class ForecastResponse(BaseModel):
    """GET /api/v1/cells/{cell_id}/forecast payload (Phase I-C contract).

    Required fields are the stable contract; extra keys (targets, confidence,
    provenance, persistence, ...) are permitted and validated as-is.
    """

    model_config = _SCHEMA_CFG

    cell_id: str
    forecast_date: str
    mode: str
    data_mode: str
    probabilities: dict[str, float]
    models: dict[str, Any]
    calibration: dict[str, Any]
    provenance: dict[str, Any]


class ModelInfoResponse(BaseModel):
    """GET /api/v1/model-info payload.

    Documents the frozen model strategy + provenance; never retrains or changes
    frozen artifacts (FREEZE_H.json / model bin files are read-only).
    """

    model_config = _SCHEMA_CFG

    app: str
    model_version: str
    freeze_file: str
    freeze_digest: str
    data_mode: str
    mode: str
    models: dict[str, Any]
    calibration: dict[str, Any]
    note: str


class GroqMeta(BaseModel):
    """Groq status block. Booleans + model name only - NEVER the API key."""

    model_config = _SCHEMA_CFG

    status: str = Field(description="ok | not_configured | error")
    model: str | None = None
    note: str | None = None


class ExplanationResponse(BaseModel):
    """GET /api/v1/cells/{cell_id}/explanation payload (Phase I-D)."""

    model_config = _SCHEMA_CFG

    cell_id: str
    forecast_date: str
    mode: str
    data_mode: str
    lang: str
    source: str = Field(description="groq | fallback")
    groq: GroqMeta
    summary: str
    why: str
    action: str
    caution: str
    probabilities: dict[str, float]
    dominant_state: str
    provenance: dict[str, Any]