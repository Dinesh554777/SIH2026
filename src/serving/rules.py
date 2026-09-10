"""Deterministic decision-support engine (v1).

Separated from ML. Maps calibrated probabilities -> band -> interpretation ->
suggested action. Versioned and inspectable; a language model (added in a later
phase, not present here) may only ever rephrase the output of this table and never
produces, modifies or overrides any number in the decision-support pipeline.
"""
from __future__ import annotations

import pandas as pd

BANDS = [
    ("low", 0.0, 0.30, "Unlikely"),
    ("moderate", 0.30, 0.60, "Possible"),
    ("high", 0.60, 0.80, "Relatively likely"),
    ("very_high", 0.80, 1.0001, "Very likely"),
]

TARGET_LABELS = {
    "onset": "Onset",
    "break": "Break",
    "revival": "Revival",
    "dry_spell": "Dry spell",
}

# ---------------------------------------------------------------------------
# v1 rules: (target, band) -> (interpretation, suggested_action)
# All actions are decision-support suggestions; none is an agronomic guarantee.
# ---------------------------------------------------------------------------
RULES_V1 = {
    "onset": {
        "low": (
            "Monsoon onset is not yet indicated by the current model state.",
            "Continue pre-sowing preparation. Do not plant based on a single wet day; wait for sustained rainfall confirmation.",
        ),
        "moderate": (
            "Onset may be approaching for the local regime.",
            "Monitor daily updates and neighbouring cells before committing field operations.",
        ),
        "high": (
            "Monsoon establishment is more likely based on the current model state.",
            "Continue monitoring for sustained rainfall confirmation before sowing or transplanting.",
        ),
        "very_high": (
            "Monsoon establishment is strongly indicated by the current model state.",
            "Proceed with sowing/transplanting only after confirming actual sustained rainfall.",
        ),
    },
    "break": {
        "low": (
            "A break in monsoon flow is not currently indicated.",
            "No immediate water-conservation pull-back is advised by this signal.",
        ),
        "moderate": (
            "Dry interruption risk is elevated.",
            "Prepare irrigation plans and monitor subsequent updates.",
        ),
        "high": (
            "A dry interruption is likely for this locality.",
            "Delay decisions that depend on sustained rainfall and monitor subsequent updates.",
        ),
        "very_high": (
            "A dry interruption is strongly indicated for this locality.",
            "Trigger irrigation scheduling and alert farmer groups where appropriate.",
        ),
    },
    "revival": {
        "low": (
            "Rainfall regime revival is not currently indicated.",
            "Maintain current dry-interruption posture until conditions change.",
        ),
        "moderate": (
            "Revival of the rainfall regime is becoming more likely.",
            "Advance preparation of field operations (e.g., transplanting/fertilizer readiness) while monitoring updated rainfall observations.",
        ),
        "high": (
            "Conditions indicate a higher likelihood of rainfall regime revival.",
            "Consider preparing field operations while monitoring updated rainfall observations.",
        ),
        "very_high": (
            "Rainfall regime revival is strongly indicated.",
            "Resume relevant field operations as appropriate, confirming with local rainfall observations.",
        ),
    },
    "dry_spell": {
        "low": (
            "Near-term agricultural dry conditions are not indicated.",
            "Normal operations; no immediate water-conservation pull-back advised.",
        ),
        "moderate": (
            "A near-term agricultural dry spell is possible.",
            "Pre-mobilize water resources and schedule irrigation windows where locally appropriate.",
        ),
        "high": (
            "Near-term dry conditions are more likely.",
            "Consider water-conservation or irrigation planning where locally appropriate.",
        ),
        "very_high": (
            "Near-term dry conditions are strongly indicated.",
            "Withhold non-essential irrigation; prioritize water for critical crop stages where locally appropriate.",
        ),
    },
}

DISCLAIMER = (
    "Decision-support suggestion, not a professional agricultural guarantee. "
    "Probabilities are calibrated outputs of frozen models and are not certainty."
)

EXPLAIN_CAVEAT = (
    "Sensitivity checks evaluate the frozen model one feature at a time (actual value "
    "vs the train median). They are descriptive only; they are NOT statements of cause."
)


def band_of(probability: float) -> str:
    p = float(probability)
    for name, lo, hi, _ in BANDS:
        if lo <= p < hi:
            return name
    return "very_high" if p >= BANDS[-1][1] else "low"


def band_meaning(name: str) -> str:
    for n, _, _, meaning in BANDS:
        if n == name:
            return meaning
    return ""


def apply_rules(probabilities: dict[str, float]) -> list[dict]:
    """Return the four cards, one per target, in a fixed order."""
    cards = []
    for target in ("onset", "break", "revival", "dry_spell"):
        p = float(probabilities[target])
        band = band_of(p)
        interpretation, action = RULES_V1[target][band]
        cards.append({
            "state": target,
            "state_label": TARGET_LABELS[target],
            "probability": round(p, 4),
            "probability_pct": round(p * 100, 1),
            "band": band,
            "band_meaning": band_meaning(band),
            "interpretation": interpretation,
            "suggested_action": action,
            "expert_validation": "Agronomic rule (v1) - recommendation only, requires expert/extension validation.",
        })
    return cards


def dominant_state(probabilities: dict[str, float]) -> str:
    # The driver of guidance is the single highest probability card.
    return max(probabilities, key=lambda k: probabilities[k])


def current_signal(row: pd.Series) -> dict:
    """Small deterministic summary of the observed state (never derived from ML)."""
    rain_t = float(row["imd_rain_t"]) if not pd.isna(row.get("imd_rain_t")) else 0.0
    sum7 = float(row["imd_sum7"]) if not pd.isna(row.get("imd_sum7")) else 0.0
    accel = float(row["th_accel"]) if not pd.isna(row.get("th_accel")) else 0.0
    dry_streak = int(row["th_dry_streak"]) if not pd.isna(row.get("th_dry_streak")) else 0
    wet_streak = int(row["th_wet_streak"]) if not pd.isna(row.get("th_wet_streak")) else 0
    wet7 = int(row["th_wetcount7"]) if not pd.isna(row.get("th_wetcount7")) else 0

    trend = "Rising" if accel > 1.0 else ("Falling" if accel < -1.0 else "Stable")
    regime = "Wetting" if wet_streak >= 1 or wet7 >= 3 else ("Drying" if dry_streak >= 3 else "Mixed")

    return {
        "rain_t_mm": round(rain_t, 2),
        "sum7_mm": round(sum7, 2),
        "rainfall_trend": trend,
        "rainfall_regime": regime,
        "wet_streak_days": wet_streak,
        "dry_streak_days": dry_streak,
        "wet_days_last7": wet7,
    }


def build_cards_with_bands(service, cell_id: str, date: pd.Timestamp, pred: dict) -> dict:
    probs = {t: pred[t]["probability"] for t in ("onset", "break", "revival", "dry_spell")}
    cards = apply_rules(probs)
    row = service.store.row(cell_id, date)

    # attach validation ECE from the freeze file for calibration context
    ece = {t: service.freeze["targets"][t]["validation_ece"] for t in probs}
    model_by_target = {t: pred[t]["model"] for t in probs}

    for card in cards:
        card["calibration_ece_val"] = float(ece[card["state"]])
        card["model"] = model_by_target[card["state"]]

    return {
        "dominant": dominant_state(probs),
        "cards": cards,
        "current_signal": current_signal(row),
        "disclaimer": DISCLAIMER,
        "evidence": service.observations_used(row),
    }