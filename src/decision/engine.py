"""Composite agricultural decision engine (protocol v2).

Merges the four calibrated probabilities with deterministic observation-derived
signals into ONE explainable decision among:

    SOW / WAIT / MONITOR / PREPARE / IRRIGATION_PREPARE

Rules are ordered by the configurable `decision_priority`; every decision carries
an evidence list ("why") assembled only from validated inputs. This module never
touches model weights or probabilities and holds no LLM dependency.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.decision.config import find_profile, load_profiles, load_rules
from src.decision.signals import false_onset_risk, monsoon_status

DECISION_LABELS = {
    "SOW": "Sow",
    "WAIT": "Wait",
    "MONITOR": "Monitor",
    "PREPARE": "Prepare",
    "IRRIGATION_PREPARE": "Irrigation prepare",
}

DECISION_ACTION = {
    "SOW": "Proceed with sowing/transplanting only when actual sustained rainfall is observed, and within the crop's sowing window.",
    "WAIT": "Hold sowing. Do not sow/transplant on a single rain event - wait for sustained rainfall confirmation.",
    "MONITOR": "Monitor daily updates and neighbouring cells before committing field operations.",
    "PREPARE": "Complete land and input readiness (seed, fertilizer, machinery) so you can sow quickly once onset is confirmed.",
    "IRRIGATION_PREPARE": "Pre-mobilize irrigation/water-conservation measures: prioritize water for critical crop stages.",
}

MONSOON_LABELS = {
    "pre_onset": "Pre-onset",
    "onset_unstable": "Onset unstable",
    "onset_stable": "Onset stable",
    "active": "Active monsoon",
    "dry_spell_risk": "Dry-spell risk",
    "break_risk": "Break risk",
    "recovery": "Recovery",
}


class DecisionError(ValueError):
    """Raised for invalid inputs to the decision engine."""


@dataclass(frozen=True)
class Evidence:
    claim: str
    status: bool
    detail: str

    def as_dict(self) -> dict:
        return {"claim": self.claim, "status": self.status, "detail": self.detail}


@dataclass(frozen=True)
class Decision:
    decision: str
    decision_label: str
    confidence: str
    monsoon_status: str
    monsoon_status_label: str
    false_onset_risk: str
    risk_summary: dict
    reasoning: list
    critical_reasons: tuple
    explanation: str
    thresholds_version: str
    mode: str = "prototype/demo"
    disclaimer: str = "Decision-support suggestion, not a professional agricultural guarantee."

    def as_dict(self) -> dict:
        return {
            "decision": self.decision,
            "decision_label": self.decision_label,
            "confidence": self.confidence,
            "monsoon_status": self.monsoon_status,
            "monsoon_status_label": MONSOON_LABELS.get(self.monsoon_status, self.monsoon_status),
            "false_onset_risk": self.false_onset_risk,
            "risk_summary": self.risk_summary,
            "reasoning": [r.as_dict() if isinstance(r, Evidence) else r for r in self.reasoning],
            "critical_reasons": list(self.critical_reasons),
            "explanation": self.explanation,
            "thresholds_version": self.thresholds_version,
            "mode": self.mode,
            "disclaimer": self.disclaimer,
        }


@dataclass(frozen=True)
class DecisionInputs:
    """Validated, named inputs handed to the engine (all optional by key)."""

    probabilities: dict = field(default_factory=dict)
    signal: dict = field(default_factory=dict)
    crop_profile: dict = field(default_factory=dict)


def _num(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _evidence_clauses(probs: dict, signal: dict, thresholds: dict, fo: str) -> list:
    t = thresholds["targets"]
    cls = [
        Evidence(
            claim="Onset probability is moderate-to-strong",
            status=_num(probs.get("onset")) >= float(t["onset"]["moderate"]),
            detail=f"onset_p = {_num(probs.get('onset')):.3f}",
        ),
        Evidence(
            claim="Recent rainfall is observed",
            status=_num(signal.get("rain_t_mm")) >= 1.0 or _num(signal.get("sum7_mm")) >= 1.0,
            detail=f"rain_t = {_num(signal.get('rain_t_mm')):.1f} mm, sum7 = {_num(signal.get('sum7_mm')):.1f} mm",
        ),
        Evidence(
            claim="Wet spell is persistent (>= required wet days)",
            status=int(_num(signal.get("wet_streak_days"))) >= int(thresholds["false_onset"]["sustained_wet_days"]),
            detail=f"wet_streak = {int(_num(signal.get('wet_streak_days')))} days",
        ),
        Evidence(
            claim="Dry-spell risk is low",
            status=_num(probs.get("dry_spell")) < float(t["dry_spell"]["high"]),
            detail=f"dry_spell_p = {_num(probs.get('dry_spell')):.3f}",
        ),
        Evidence(
            claim="Break risk is low",
            status=_num(probs.get("break")) < float(t["break"]["high"]),
            detail=f"break_p = {_num(probs.get('break')):.3f}",
        ),
        Evidence(
            claim="False-onset warning is not high",
            status=fo != "high",
            detail=f"derived false-onset risk = {fo}",
        ),
    ]
    # Keep only entries that actually carry signal for the reader.
    return cls


def build_decision(
    probabilities: dict,
    signal: dict,
    crop_profile: dict | None = None,
    rules=None,
    mode: str = "prototype/demo",
) -> Decision:
    """Produce a deterministic decision from probabilities + observation signal.

    `rules` (optional) is the loaded thresholds object (data/decision/decision_rules.json);
    if omitted it is loaded from the configured path. `signal` must contain at least
    rain_t_mm/sum7_mm/wet_streak_days/dry_streak_days/wet_days_last7 (see
    serving.rules.current_signal); it is intentionally small and freely testable.
    """
    if not isinstance(probabilities, dict) or not probabilities:
        raise DecisionError("probabilities dict required")
    if not isinstance(signal, dict) or not signal:
        raise DecisionError("signal dict required")

    rules = rules if rules is not None else load_rules()
    version = rules.get("version", "?")
    prio = list(rules.get("decision_priority", []))
    fo = false_onset_risk(probabilities, signal, rules)
    status = monsoon_status(probabilities, signal, rules, fo.level)

    t = rules["targets"]
    onset = _num(probabilities.get("onset"))
    dry_p = _num(probabilities.get("dry_spell"))
    break_p = _num(probabilities.get("break"))
    wet_streak = int(_num(signal.get("wet_streak_days")))
    wet7 = int(_num(signal.get("wet_days_last7")))
    dry_streak = int(_num(signal.get("dry_streak_days")))

    # Rule evaluation (ordered by configured priority).
    decision = "MONITOR"
    why: list[str] = []

    for key in prio:
        if key == "wait_false_onset":
            if fo.level == "high":
                decision, why = "WAIT", fo.reasons + (
                    "Await sustained rainfall confirmation before any field commitment.",
                )
                break
        elif key == "irrigation_prepare":
            if dry_p >= float(t["dry_spell"]["high"]) and (wet_streak >= 1 or wet7 >= 1):
                decision, why = "IRRIGATION_PREPARE", (
                    "Elevated dry-spell risk following a wet recent period.",
                    "Prioritize water conservation and targeted irrigation for critical crop stages.",
                )
                break
        elif key == "sow":
            sow_conf = 0.6
            if crop_profile:
                sow_conf = float(crop_profile.get("sow_confidence_needed", 0.6))
            if onset >= sow_conf and fo.level != "high" and dry_p < float(t["dry_spell"]["high"]):
                decision, why = "SOW", (
                    f"Onset probability is strong ({onset:.0%} >= {sow_conf:.0%} crop threshold).",
                    "False-onset risk is contained; dry-spell risk is below the high band.",
                    "Sow only after confirming actual sustained rainfall in the field.",
                )
                break
        elif key == "prepare":
            if onset >= float(t["onset"]["moderate"]):
                decision, why = "PREPARE", (
                    "Onset signal has crossed the moderate threshold.",
                    "Finish land and input readiness so sowing can follow confirmation quickly.",
                )
                break
        elif key == "monitor":
            if onset < float(t["onset"]["moderate"]):
                decision, why = "MONITOR", (
                    "Onset signal below moderate threshold.",
                    "Conditions may still change; continue daily monitoring.",
                )
                break

    if not why:
        decision, why = "MONITOR", ("No dominant signal; continue to monitor conditions.",)

    # Confidence (deterministic, agreement + distance from configured thresholds).
    confidence = _derive_confidence(decision, fo.level, onset, dry_p, signal, t)

    evidence = _evidence_clauses(probabilities, signal, rules, fo.level)
    reasoning = list(evidence)
    for line in why:
        reasoning.append(Evidence(claim=line, status=True, detail=""))
    explanation = "\n".join(f"  - {line}" for line in why)

    risk_summary = {
        "onset": {"probability": round(onset, 4), "band": _risk_band(onset, "onset", rules)},
        "dry_spell": {"probability": round(dry_p, 4), "band": _risk_band(dry_p, "dry_spell", rules)},
        "break": {"probability": round(break_p, 4), "band": _risk_band(break_p, "break", rules)},
        "false_onset_derived": {"level": fo.level},
    }

    return Decision(
        decision=decision,
        decision_label=DECISION_LABELS.get(decision, decision),
        confidence=confidence,
        monsoon_status=status,
        monsoon_status_label=MONSOON_LABELS.get(status, status),
        false_onset_risk=fo.level,
        risk_summary=risk_summary,
        reasoning=reasoning,
        critical_reasons=tuple(why),
        explanation=explanation,
        thresholds_version=version,
        mode=mode,
    )


def _risk_band(probability: float, target: str, rules: dict) -> str:
    t = rules["targets"].get(target, {})
    p = _num(probability)
    high = float(t.get("high", 0.6))
    moderate = float(t.get("moderate", 0.3))
    if p >= high:
        return "high"
    if p >= moderate:
        return "moderate"
    return "low"


def _derive_confidence(decision, fo, onset, dry_p, signal, t) -> str:
    """Deterministic confidence: strong when threshold distance + agreement is clear."""
    wet_streak = int(_num(signal.get("wet_streak_days")))
    if decision == "WAIT" and fo == "high":
        return "high"
    if decision == "SOW" and onset >= float(t["onset"]["strong"]) and fo == "low":
        return "high"
    if decision in ("MONITOR", "PREPARE", "IRRIGATION_PREPARE"):
        return "medium"
    return "medium"


def decision_from_serving(prediction_bundle: dict, crop: str | None = None,
                          season: str | None = None, mode: str = "prototype/demo") -> Decision:
    """Adapt the serving-layer bundle (rules.build_cards_with_bands output) to a Decision.

    `prediction_bundle` must contain `cards` (with .probability per state) and
    `current_signal`. Crop/season select a representative agricultural profile
    used only for advisory wording and the per-crop sow-confidence threshold.
    """
    try:
        probs = {
            card["state"]: float(card["probability"])
            for card in prediction_bundle["cards"]
        }
        signal = dict(prediction_bundle["current_signal"])
    except (KeyError, TypeError) as exc:
        raise DecisionError(f"serving bundle missing required keys: {exc}") from exc

    profiles = load_profiles()
    profile = find_profile(profiles, crop=crop, season=season)
    return build_decision(probs, signal, crop_profile=profile or {}, mode=mode)