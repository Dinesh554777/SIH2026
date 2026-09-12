"""Live-ingestion configuration (Gate J1).

Reads environment variables (with .env support via the existing loader used by
src.database.config) WITHOUT breaking historical mode:

    FORECAST_MODE=historical        # historical | live   (default historical)
    LIVE_DATA_SOURCE=imd            # imd | mock
    LIVE_SOURCE_URL=                # optional source URL override (IMD POST endpoint by default)
    LIVE_REQUEST_TIMEOUT_SECONDS=30
    LIVE_MAX_RETRIES=2              # bounded bursts for transient failures
    MAX_OBSERVATION_AGE_HOURS=48    # freshness threshold
    LIVE_ALLOW_MOCK=0               # 1 enables the deterministic MOCK/TEST-ONLY source

Credentials are NEVER defined here; they belong only in a local (git-ignored) .env.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from src.database.config import _load_envfile  # reuse the existing .env loader
from src.ingestion.errors import ConfigurationError

_load_envfile()

ALLOWED_MODES = ("historical", "live")
ALLOWED_SOURCES = ("imd", "mock")


def _parse_float(env: dict, key: str, default: float, lo: float, hi: float, name: str) -> float:
    raw = env.get(key, str(default))
    try:
        v = float(raw)
    except (TypeError, ValueError):
        raise ConfigurationError(f"{key} must be a number, got {raw!r}")
    if not (lo <= v <= hi):
        raise ConfigurationError(f"{name} out of range [{lo}, {hi}]: {v}")
    return v


def _parse_int(env: dict, key: str, default: int, lo: int, hi: int, name: str) -> int:
    raw = env.get(key, str(default))
    try:
        v = int(raw)
    except (TypeError, ValueError):
        raise ConfigurationError(f"{key} must be an integer, got {raw!r}")
    if not (lo <= v <= hi):
        raise ConfigurationError(f"{name} out of range [{lo}, {hi}]: {v}")
    return v


@dataclass(frozen=True)
class LiveConfig:
    """Validated live-ingestion configuration (all values frozen defaults)."""

    forecast_mode: str = "historical"
    live_data_source: str = "imd"
    source_url: str | None = None
    request_timeout_seconds: float = 30.0
    max_retries: int = 2
    max_observation_age_hours: float = 48.0
    future_tolerance_seconds: float = 3600.0
    allow_mock: bool = False


def load_live_config(env: dict | None = None) -> LiveConfig:
    """Build a validated LiveConfig from an env mapping (defaults: os.environ).

    Raises ConfigurationError on any invalid value; historical mode always stays
    the safe default.
    """
    e = os.environ if env is None else env

    mode = str(e.get("FORECAST_MODE", "historical")).strip().lower()
    if mode not in ALLOWED_MODES:
        raise ConfigurationError(
            f"FORECAST_MODE={mode!r} not in {ALLOWED_MODES}")

    source = str(e.get("LIVE_DATA_SOURCE", "imd")).strip().lower()
    if source not in ALLOWED_SOURCES:
        raise ConfigurationError(
            f"LIVE_DATA_SOURCE={source!r} not in {ALLOWED_SOURCES}")

    allow_mock = str(e.get("LIVE_ALLOW_MOCK", "0")).strip().lower() in ("1", "true", "yes", "on")
    if source == "mock" and not allow_mock:
        raise ConfigurationError(
            "LIVE_DATA_SOURCE=mock requires LIVE_ALLOW_MOCK=1 (MOCK / TEST ONLY source)")

    url = e.get("LIVE_SOURCE_URL") or None
    if url:
        url = url.strip()
        if not (url.startswith("https://") or url.startswith("http://")):
            raise ConfigurationError(
                "LIVE_SOURCE_URL must be an absolute http(s) URL; local file paths "
                "are not a live source and are rejected")

    return LiveConfig(
        forecast_mode=mode,
        live_data_source=source,
        source_url=url,
        request_timeout_seconds=_parse_float(
            e, "LIVE_REQUEST_TIMEOUT_SECONDS", 30.0, 1.0, 600.0, "request timeout"),
        max_retries=_parse_int(
            e, "LIVE_MAX_RETRIES", 2, 0, 10, "max retries"),
        max_observation_age_hours=_parse_float(
            e, "MAX_OBSERVATION_AGE_HOURS", 48.0, 1.0, 24 * 365.0, "max observation age"),
        future_tolerance_seconds=_parse_float(
            e, "FUTURE_TOLERANCE_SECONDS", 3600.0, 0.0, 24 * 3600.0, "future tolerance"),
        allow_mock=allow_mock,
    )