"""Real-source connectivity probe for the J1 report (runnable, internet required).

Usage:
    python -m src.ingestion.connectivity

Fetches the latest IMD live-rainfall day for the pilot grid directly from the
operational IMD Pune endpoint and prints a structured result. Intentionally
does NOT write to the database. Timeouts are kept small (default 12s) so BLOCKED
facilities are reported quickly and honestly.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone

import pandas as pd

from src.ingestion.clients.imd import IMDGridSource
from src.ingestion.clients.mock import MockObservationSource
from src.ingestion.config import load_live_config
from src.ingestion.errors import IngestionError
from src.ingestion.normalizer import CellMapper, normalize_batch
from src.ingestion.service import IngestionService

MIN_PILOT_CELLS = 300  # a connectivity check on < 300 cells is not representative


def _load_pilot_cells() -> pd.DataFrame:
    from src.serving.registry import default_registry

    return default_registry().cells


def main() -> int:
    now = datetime.now(timezone.utc)
    cfg = load_live_config()
    print(f"[probe] now={now.isoformat()} forecast_mode={cfg.forecast_mode} "
          f"source={cfg.live_data_source}")

    cells = _load_pilot_cells()
    mapper = CellMapper(cells)
    print(f"[probe] pilot cells resolved: {len(cells)} (expect >= {MIN_PILOT_CELLS})")
    if len(cells) < MIN_PILOT_CELLS:
        print("[probe] RESULT: CONFIG ABORTED — insufficient pilot cells")
        return 2

    source: IMDGridSource | MockObservationSource
    try:
        if cfg.live_data_source == "mock":
            source = MockObservationSource(cells)
            print("[probe] NOTE: MOCK source selected — this is a determinism "
                  "self-check, NOT a real connectivity attempt")
        else:
            source = IMDGridSource(cells, url=cfg.source_url,
                                   timeout=cfg.request_timeout_seconds)
    except IngestionError as exc:
        print(f"[probe] RESULT: CONFIG ERROR — {exc}")
        return 2

    print(f"[probe] source={source.name} url={getattr(source, 'post_url', 'n/a')} "
          f"is_mock={source.is_mock}")
    svc = IngestionService(source, mapper, max_age_hours=cfg.max_observation_age_hours,
                           future_tolerance_seconds=cfg.future_tolerance_seconds,
                           max_retries=cfg.max_retries, allow_mock=cfg.allow_mock)

    result = svc.ingest(now=now)
    print("RESULT:")
    for k, v in result.as_dict().items():
        if k not in ("observations", "rejected"):
            print(f"  {k}: {v}")
    print(f"  source_is_mock: {source.is_mock}")

    if result.status != "failed":
        print("[probe] TYPE: OPERATIONAL (real data received)" if not source.is_mock
              else "[probe] TYPE: MOCK SELF-CHECK")
        print(f"[probe] ENDPOINT STATUS: OPERATIONAL" if not source.is_mock
              else "[probe] ENDPOINT STATUS: MOCK")
        return 0
    error = result.errors[0] if result.errors else "unknown"
    if isinstance(error, str) and "(source=" in error:
        print("[probe] TYPE: LIVE CONNECTIVITY")
        print("[probe] ENDPOINT STATUS: BLOCKED")
        print(f"[probe] REASON: {error}")
    else:
        print(f"[probe] TYPE: LIVE CONNECTIVITY / VALIDATION")
        print("[probe] ENDPOINT STATUS: BLOCKED")
        print(f"[probe] REASON: {error}")
    return 1


if __name__ == "__main__":
    try:
        rc = main()
    except Exception as exc:  # noqa: BLE001 — top-level probe always exits cleanly
        print(f"[probe] EXCEPTION: {type(exc).__name__}: {exc}")
        rc = 3
    sys.exit(rc)