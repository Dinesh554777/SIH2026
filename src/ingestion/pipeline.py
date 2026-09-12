"""J1 ingestion pipeline wired to PostgreSQL persistence (Phase J2).

Flow (this gate only — NO features/models/forecasts):

    Source -> normalize -> validate -> persistence -> ingestion-run status

    create_ingestion_run(RUNNING)
    IngestionService.ingest()
    bulk_insert_observations(valid rows)   [idempotent ON CONFLICT DO NOTHING]
    update_ingestion_run(SUCCESS / PARTIAL / BLOCKED / FAILED, counts + error)

When the source is unreachable (SourceUnavailableError) the run is recorded as
BLOCKED with the real error preserved and ZERO observations inserted. No
fallback to historical files, no fabricated data. The MOCK source stays
gate-kept behind LIVE_ALLOW_MOCK=1 (allow_mock=True) and is only ever persisted
through this same repository path, marked source=mock-sim.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.database.ingestion_repository import (bulk_insert_observations,
                                               create_ingestion_run,
                                               ingestion_status_for_result,
                                               update_ingestion_run)
from src.ingestion.normalizer import CellMapper
from src.ingestion.service import IngestionService

logger = logging.getLogger("sih2026.ingestion.pipeline")


class IngestionPipeline:
    def __init__(self, source, mapper: CellMapper, *, max_age_hours: float = 48.0,
                 future_tolerance_seconds: float = 3600.0, max_retries: int = 2,
                 allow_mock: bool = False, run_metadata: dict | None = None):
        self.service = IngestionService(
            source, mapper, max_age_hours=max_age_hours,
            future_tolerance_seconds=future_tolerance_seconds,
            max_retries=max_retries, allow_mock=allow_mock)
        self.run_metadata = dict(run_metadata or {})
        try:
            self._describe = self.service.source.describe()
        except Exception:
            self._describe = {"name": self.service.source.name}

    def run(self, session: Session, now: datetime | None = None) -> dict:
        """Execute one ingestion cycle and persist its results atomically.

        Returns a summary dict: run_id, recorded_status, inserted count, and the
        full IngestionResult.as_dict().
        """
        now = now or datetime.now(timezone.utc)
        source = self.service.source

        # phase 1: durable RUNNING marker (committed immediately so a crash is auditable)
        run = create_ingestion_run(
            session, source=source.name, started_at=now,
            metadata={"describe": self._describe, **self.run_metadata})
        session.commit()
        run_id = int(run.id)

        # phase 2: fetch + normalize + validate (no DB)
        result = self.service.ingest(now=now)

        # phase 3: persist observations + close the run in ONE transaction
        inserted = 0
        status = "FAILED"
        try:
            inserted = bulk_insert_observations(
                session, [o for o in result.observations])
            status, error_type = ingestion_status_for_result(result)
            update_ingestion_run(
                session, run_id,
                status=status,
                completed_at=now,
                rows_received=result.rows_received,
                rows_inserted=inserted,
                rows_rejected=result.rows_rejected,
                error_type=error_type,
                error_message="\n".join(result.errors) or None,
                metadata={
                    "describe": self._describe,
                    "freshness": result.freshness,
                    "rows_valid": len(result.observations),
                    "source_is_mock": source.is_mock,
                    **self.run_metadata,
                },
            )
            session.commit()
        except Exception as exc:  # FK/DB failure -> rollback + FAILED
            session.rollback()
            logger.exception("ingestion persistence failed run=%s", run_id)
            status = "FAILED"
            try:
                update_ingestion_run(
                    session, run_id, status=status, completed_at=now,
                    rows_received=result.rows_received, rows_inserted=0,
                    rows_rejected=result.rows_rejected,
                    error_type=type(exc).__name__, error_message=str(exc),
                    metadata={"describe": self._describe, "source_is_mock": source.is_mock,
                              **self.run_metadata})
                session.commit()
            except Exception:
                session.rollback()

        return {
            "run_id": run_id,
            "recorded_status": status,
            "inserted": inserted,
            "result": result.as_dict(),
        }


def run_pipeline_once(session: Session, *, source, mapper: CellMapper,
                      now: datetime | None = None, **kwargs) -> dict:
    return IngestionPipeline(source, mapper, **kwargs).run(session, now=now)