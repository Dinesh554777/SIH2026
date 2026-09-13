"""Decision-support persistence (Product layer, migration 0004 tables).

Idempotent records for risk_assessments, agricultural_context, advisory_deliveries
and monsoon_events. All inputs are application-validated before writing; ORM
constraints are the final safety net. Names use the decision-engine vocabulary
(decision codes, risk levels, location types).
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.database.models import (AdvisoryDelivery, AgriculturalContext,
                                 DECISION_CODES, MonsoonEvent,
                                 RISK_LEVELS, RiskAssessment)

_LOCATION_TYPES = ("state", "district", "block", "village", "cell")


class DecisionIntegrityError(ValueError):
    """Raised for inconsistent decision-layer references (fail loud)."""


def _require_location(location_type: str, location_id: str) -> None:
    if location_type not in _LOCATION_TYPES:
        raise DecisionIntegrityError(f"invalid location_type: {location_type}")
    if not location_id or not str(location_id).strip():
        raise DecisionIntegrityError("location_id must be non-empty")


def record_risk_assessment(session: Session, *, location_type: str, location_id: str,
                           decision: str, confidence: str, monsoon_status: str,
                           false_onset_risk: str, onset_probability: float,
                           dry_spell_probability: float, break_probability: float,
                           risk_summary: dict, evidence: dict,
                           thresholds_version: str,
                           mode: str = "prototype/demo",
                           forecast_id: int | None = None,
                           cell_id: str | None = None) -> int:
    """Persist one composite decision. Returns the new risk_assessment id."""
    _require_location(location_type, location_id)
    if decision not in DECISION_CODES:
        raise DecisionIntegrityError(f"invalid decision: {decision}")
    if false_onset_risk not in RISK_LEVELS:
        raise DecisionIntegrityError(f"invalid false_onset_risk: {false_onset_risk}")
    ra = RiskAssessment(
        forecast_id=forecast_id, location_type=location_type, location_id=location_id,
        cell_id=cell_id, decision=decision, confidence=confidence,
        monsoon_status=monsoon_status, false_onset_risk=false_onset_risk,
        onset_probability=onset_probability,
        dry_spell_probability=dry_spell_probability,
        break_probability=break_probability, risk_summary=risk_summary,
        evidence=evidence, thresholds_version=thresholds_version, mode=mode,
    )
    session.add(ra)
    session.flush()
    return ra.id


def record_advisory_delivery(session: Session, *, risk_assessment_id: int,
                             location_type: str, location_id: str, decision: str,
                             channel: str, language: str,
                             status: str = "generated",
                             recipient_scope: str | None = None,
                             issued_by: str | None = None,
                             payload: dict | None = None,
                             mock_notice: str | None = None,
                             delivered_at: datetime | None = None) -> int:
    """Persist one advisory dispatch traceability row."""
    _require_location(location_type, location_id)
    if channel not in ("field_worker", "panchayat", "notice_print", "sms",
                       "ivr", "whatsapp", "fpo"):
        raise DecisionIntegrityError(f"invalid channel: {channel}")
    if language not in ("en", "ta", "en,ta"):
        raise DecisionIntegrityError(f"invalid language: {language}")
    row = AdvisoryDelivery(
        risk_assessment_id=risk_assessment_id, location_type=location_type,
        location_id=location_id, decision=decision, channel=channel,
        language=language, status=status, recipient_scope=recipient_scope,
        issued_by=issued_by, payload=payload, mock_notice=mock_notice,
        delivered_at=delivered_at,
    )
    session.add(row)
    session.flush()
    return row.id


def upsert_agricultural_context(session: Session, *, location_type: str,
                                location_id: str, crop: str, season: str,
                                sowing_window_start: str, sowing_window_end: str,
                                sow_confidence_needed: float,
                                dry_spell_sensitivity: str,
                                irrigation_availability: str,
                                rainfall_requirement_mm: float | None = None,
                                soil: str | None = None,
                                source: str = "demo/prototype") -> None:
    """Idempotently add/refresh one crop-season context row."""
    _require_location(location_type, location_id)
    table = AgriculturalContext.__table__
    vals = {
        "location_type": location_type, "location_id": location_id,
        "crop": crop, "season": season,
        "sowing_window_start": sowing_window_start,
        "sowing_window_end": sowing_window_end,
        "sow_confidence_needed": sow_confidence_needed,
        "dry_spell_sensitivity": dry_spell_sensitivity,
        "irrigation_availability": irrigation_availability,
        "rainfall_requirement_mm": rainfall_requirement_mm,
        "soil": soil, "source": source,
    }
    vals = {k: v for k, v in vals.items() if k in table.columns and v is not None}
    stmt = insert(table).values(**vals).on_conflict_do_update(
        index_elements=["location_type", "location_id", "crop", "season"],
        set_={k: vals[k] for k in vals if k not in
              ("location_type", "location_id", "crop", "season")},
    )
    session.execute(stmt)


def record_monsoon_event(session: Session, *, location_type: str, location_id: str,
                         event_type: str, start_date: datetime,
                         risk_level: str = "medium",
                         end_date: datetime | None = None,
                         note: str | None = None,
                         cell_id: str | None = None,
                         source: str = "decision-engine") -> int:
    """Persist one event-timeline row."""
    _require_location(location_type, location_id)
    if event_type not in ("onset", "false_onset", "dry_spell", "break", "recovery"):
        raise DecisionIntegrityError(f"invalid event_type: {event_type}")
    row = MonsoonEvent(location_type=location_type, location_id=location_id,
                       cell_id=cell_id, event_type=event_type, start_date=start_date,
                       end_date=end_date, risk_level=risk_level, note=note,
                       source=source)
    session.add(row)
    session.flush()
    return row.id


def latest_risk_assessment(session: Session, location_type: str,
                           location_id: str) -> RiskAssessment | None:
    """Most recent composite decision for a location (or None)."""
    return session.execute(
        select(RiskAssessment)
        .where(RiskAssessment.location_type == location_type,
               RiskAssessment.location_id == location_id)
        .order_by(RiskAssessment.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()