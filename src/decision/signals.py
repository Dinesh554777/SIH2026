"""Derived monsoon signals used by the decision engine.

Only validated model outputs and observation-derived signals are consumed here.
No probability is ever fabricated: the false-onset risk below is a deterministic
heuristic (documented and auditable) - there is no trained p_false_onset target.
"""
from __future__ import annotations

from dataclasses import dataclass

MONSOON_STATUSES = {
    "pre_onset": "Pre-onset",
    "onset_unstable": "Onset unstable",
    "onset_stable": "Onset stable",
    "active": "Active monsoon",
    "dry_spell_risk": "Dry-spell risk",
    "break_risk": "Break risk",
    "recovery": "Recovery",
}

FALSE_ONSET_LEVELS = ("low", "medium", "high")


@dataclass(frozen=True)
class FalseOnsetRisk:
    level: str
    reasons: tuple[str, ...]


def _num(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def false_onset_risk(probs: dict, signal: dict, thresholds: dict) -> FalseOnsetRisk:
    """Derive false-onset risk from validated signals (never a trained probability).

    elevated   : recent rainfall clearly triggered (single-day >= threshold or
                    7-day accumulation >= threshold) while the model's onset
                    probability stays below 'strong'.
    weak_persist: observed wet streak and wet-days-in-7 are short, so the wet
                    spell has not yet become sustained.
    drying     : the observed streak turned dry again and/or dry-spell risk is
                    elevated - the wet perturbation is eroding.
    """
    fo = thresholds["false_onset"]
    elevated_rain_mm = float(fo["elevated_rain_mm"])
    sustained_wet_days = int(fo["sustained_wet_days"])
    wet_days7_needed = int(fo["wet_days7_needed"])
    escalation_dry_streak = int(fo["escalation_dry_streak"])

    onset_prob = _num(probs.get("onset"))
    onset_strong = float(thresholds["targets"]["onset"]["strong"])

    rain_t = _num(signal.get("rain_t_mm"))
    sum7 = _num(signal.get("sum7_mm"))
    wet_streak = int(_num(signal.get("wet_streak_days")))
    wet7 = int(_num(signal.get("wet_days_last7")))
    dry_streak = int(_num(signal.get("dry_streak_days")))
    dry_spell_prob = _num(probs.get("dry_spell"))
    dry_high = float(thresholds["targets"]["dry_spell"]["high"])

    elevated = (rain_t >= elevated_rain_mm or sum7 >= elevated_rain_mm) and onset_prob < onset_strong
    weak_persist = wet_streak < sustained_wet_days or wet7 < wet_days7_needed
    drying = dry_streak >= escalation_dry_streak or dry_spell_prob >= dry_high

    reasons: list[str] = []
    if not elevated:
        level = "low"
        reasons.append("No rainfall trigger observed; onset probability not subdued by a recent wet spike.")
    elif not weak_persist:
        level = "low"
        reasons.append("Recent rainfall is sustained, which suppresses false-onset risk.")
    elif drying:
        level = "high"
        reasons.append("Recent rainfall spike is not sustained (fails continuous-wetness persistence).")
        reasons.append("A dry streak and/or elevated dry-spell risk is already reasserting.")
    else:
        level = "medium"
        reasons.append("Recent rainfall spike but persistence not yet confirmed within review window.")

    return FalseOnsetRisk(level=level, reasons=tuple(reasons))


def monsoon_status(probs: dict, signal: dict, thresholds: dict, fo_level: str) -> str:
    """Coarse deterministic status for the advisory header."""
    onset = _num(probs.get("onset"))
    break_p = _num(probs.get("break"))
    dry_p = _num(probs.get("dry_spell"))
    revival = _num(probs.get("revival"))

    t = thresholds["targets"]
    onset_mod = float(t["onset"]["moderate"])
    onset_strong = float(t["onset"]["strong"])
    break_high = float(t["break"]["high"])
    dry_high = float(t["dry_spell"]["high"])
    revival_mod = float(t["revival"]["moderate"])

    wet_streak = int(_num(signal.get("wet_streak_days")))
    wet7 = int(_num(signal.get("wet_days_last7")))
    dry_streak = int(_num(signal.get("dry_streak_days")))

    if dry_p >= dry_high and dry_streak >= 1:
        return "dry_spell_risk"
    if onset >= onset_strong and fo_level == "low" and (wet_streak >= 1 or wet7 >= 3):
        return "onset_stable"
    if break_p >= break_high:
        return "break_risk"
    if revival >= revival_mod:
        return "recovery"
    if onset >= onset_mod:
        return "onset_unstable"
    return "pre_onset"