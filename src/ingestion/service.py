"""Ingestion orchestration service (Gate J1).

Responsibilities (J1 scope only — no forecasting, no DB writes):
- fetch from the configured ObservationSource with bounded retries for
  transient failures (SourceUnavailableError / SourceResponseError ONLY)
- validate + normalize into the project Observation model
- classify batch freshness
- structured logging (never logs secrets)
- block persisted use of the MOCK source unless allow_mock=True

next gate (J2) adds PostgreSQL persistence of IngestionResult.observations.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from src.ingestion.clients.base import ObservationSource
from src.ingestion.errors import RETRIABLE_ERRORS, ValidationError
from src.ingestion.models import (FRESHNESS_UNAVAILABLE, IngestionResult)
from src.ingestion.normalizer import CellMapper, normalize_batch
from src.ingestion.validators import classify_freshness

logger = logging.getLogger("sih2026.ingestion")

MAX_MOCK_GUARD = ("refusing to ingest observations from a MOCK / TEST-ONLY source; "
                  "if you really intend this (e.g. connector smoke test), set "
                  "allow_mock=True on the service")


class IngestionService:
    def __init__(self, source: ObservationSource, mapper: CellMapper,
                 max_age_hours: float = 48.0,
                 future_tolerance_seconds: float = 3600.0,
                 max_retries: int = 2, allow_mock: bool = False):
        self.source = source
        self.mapper = mapper
        self.max_age_hours = max_age_hours
        self.future_tolerance_seconds = future_tolerance_seconds
        self.max_retries = int(max_retries)
        self.allow_mock = bool(allow_mock)

    # ------------------------------------------------------------------ ingest
    def ingest(self, now: datetime | None = None) -> IngestionResult:
        """Run one full ingestion cycle. Never raises source errors; returns a
        structured IngestionResult (validation failures are returned, not thrown)."""
        now = now or datetime.now(timezone.utc)
        t0 = time.perf_counter()
        if self.source.is_mock and not self.allow_mock:
            res = IngestionResult(source=self.source.name, status="failed",
                                  errors=[MAX_MOCK_GUARD], freshness=FRESHNESS_UNAVAILABLE)
            res.duration_seconds = time.perf_counter() - t0
            logger.warning("ingestion guard: %s", MAX_MOCK_GUARD)
            return res

        logger.info("ingestion started source=%s", self.source.name)
        try:
            response = self._fetch_with_retry(now)
        except RETRIABLE_ERRORS as exc:
            res = IngestionResult(source=self.source.name, status="failed",
                                  errors=[f"{type(exc).__name__}: {exc}"],
                                  metadata=self.source.describe(),
                                  freshness=FRESHNESS_UNAVAILABLE)
            res.duration_seconds = time.perf_counter() - t0
            logger.error("ingestion failed source=%s error=%s", self.source.name, exc)
            return res

        try:
            valid, rejected, parsed_times = normalize_batch(
                response.rows, source=response.source,
                retrieved_at=response.retrieved_at,
                mapper=self.mapper,
                now=now,
                max_age_hours=self.max_age_hours,
                future_tolerance_seconds=self.future_tolerance_seconds,
            )
        except (ValueError, TypeError) as exc:
            res = IngestionResult(source=self.source.name, status="failed",
                                  errors=[f"normalization failed: {exc}"],
                                  rows_received=len(response.rows),
                                  metadata=response.metadata,
                                  freshness=FRESHNESS_UNAVAILABLE)
            res.duration_seconds = time.perf_counter() - t0
            logger.error("ingestion normalization failed source=%s error=%s",
                         self.source.name, exc)
            return res

        latest = max(parsed_times, default=None)
        status = ("success" if valid and not rejected
                  else "partial" if valid else "failed")
        freshness = classify_freshness(
            latest, now, self.max_age_hours, self.future_tolerance_seconds)

        res = IngestionResult(
            source=response.source,
            status=status,
            retrieved_at=response.retrieved_at,
            observation_time=latest,
            rows_received=len(response.rows),
            rows_valid=len(valid),
            rows_rejected=len(rejected),
            freshness=freshness,
            errors=[],
            observations=valid,
            rejected=rejected,
            metadata=response.metadata,
        )
        res.duration_seconds = time.perf_counter() - t0
        logger.info(
            "ingestion completed source=%s status=%s rows=%d valid=%d rejected=%d "
            "freshness=%s duration=%.2fs",
            res.source, res.status, res.rows_received, res.rows_valid,
            res.rows_rejected, res.freshness, res.duration_seconds)
        return res

    # ------------------------------------------------------------------ retry
    def _fetch_with_retry(self, now: datetime):
        """Bounded retry for TRANSIENT source failures only.

        Permanent configuration/semantic errors (ValidationError) are raised
        immediately with no retry; transient network/http/malformed-response
        errors are retried up to max_retries times (attempts = max_retries + 1).
        """
        attempt = 0
        while True:
            try:
                return self.source.fetch(now=now)
            except RETRIABLE_ERRORS as exc:
                if attempt >= self.max_retries:
                    raise
                attempt += 1
                logger.warning("source fetch retry source=%s attempt=%d/%d error=%s",
                               self.source.name, attempt, self.max_retries, type(exc).__name__)
            except ValidationError:
                raise