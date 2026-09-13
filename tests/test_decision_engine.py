"""Decision engine, advisory & delivery tests (offline, no DB).

Covers the deterministic composite decision (SOW/WAIT/MONITOR/PREPARE/
IRRIGATION_PREPARE), the derived false-onset signal, evidence ("why") and the
bilingual advisory + last-mile channel generators. No model, no network, no DB.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.decision.advisory import (TA_ACTION, TA_DECISION, TA_WHY,
                                   generate_village_advisory)
from src.decision.config import load_profiles, load_rules, find_profile
from src.decision.delivery import CHANNELS, deliver, ivr_script
from src.decision.engine import DECISION_LABELS, DecisionError, build_decision
from src.decision.signals import false_onset_risk, monsoon_status

RULES = load_rules()
PROFILES = load_profiles()
PADDY = find_profile(PROFILES, crop="paddy", season="kharif")


def _sig(rain_t=0.0, sum7=0.0, trend="Stable", regime="Mixed",
         wet_streak=0, dry_streak=0, wet7=0) -> dict:
    return {
        "rain_t_mm": rain_t, "sum7_mm": sum7, "rainfall_trend": trend,
        "rainfall_regime": regime, "wet_streak_days": wet_streak,
        "dry_streak_days": dry_streak, "wet_days_last7": wet7,
    }


# ------------------------------------------------------- false-onset signal
def test_false_onset_low_when_no_trigger():
    probs = {"onset": 0.3, "dry_spell": 0.2, "break": 0.1}
    fo = false_onset_risk(probs, _sig(), RULES)
    assert fo.level == "low"
    assert fo.reasons


def test_false_onset_high_on_spike_then_drying():
    probs = {"onset": 0.25, "dry_spell": 0.7, "break": 0.2}
    sig = _sig(rain_t=40.0, sum7=55.0, wet_streak=1, dry_streak=4, wet7=1)
    fo = false_onset_risk(probs, sig, RULES)
    assert fo.level == "high"


def test_false_onset_suppressed_by_sustained_wet():
    probs = {"onset": 0.25, "dry_spell": 0.3, "break": 0.2}
    sig = _sig(rain_t=12.0, sum7=90.0, wet_streak=5, wet7=5)
    fo = false_onset_risk(probs, sig, RULES)
    assert fo.level == "low"


# ------------------------------------------------------------- monsoon status
def test_monsoon_status_stable_onset():
    probs = {"onset": 0.7, "dry_spell": 0.1, "break": 0.1, "revival": 0.1}
    sig = _sig(rain_t=15.0, sum7=80.0, wet_streak=2, wet7=4)
    assert monsoon_status(probs, sig, RULES, "low") == "onset_stable"


def test_monsoon_status_dry_spell_takes_precedence():
    probs = {"onset": 0.7, "dry_spell": 0.7, "break": 0.1, "revival": 0.1}
    sig = _sig(rain_t=15.0, sum7=80.0, wet_streak=2, wet7=4, dry_streak=2)
    assert monsoon_status(probs, sig, RULES, "low") == "dry_spell_risk"


# ------------------------------------------------------------ composite decision
def test_decision_wait_on_high_false_onset():
    probs = {"onset": 0.25, "dry_spell": 0.7, "break": 0.2, "revival": 0.1}
    sig = _sig(rain_t=40.0, sum7=55.0, wet_streak=1, dry_streak=4, wet7=1)
    d = build_decision(probs, sig, crop_profile=PADDY)
    assert d.decision == "WAIT"
    assert d.false_onset_risk == "high"
    assert d.monsoon_status in ("break_risk", "dry_spell_risk")
    assert any(ev.status for ev in d.reasoning)
    assert len(d.critical_reasons) > 0


def test_decision_sow_on_strong_sustained_onset():
    probs = {"onset": 0.7, "dry_spell": 0.2, "break": 0.15, "revival": 0.1}
    sig = _sig(rain_t=12.0, sum7=85.0, wet_streak=3, wet7=4)
    d = build_decision(probs, sig, crop_profile=PADDY)
    assert d.decision == "SOW"


def test_decision_prepare_on_moderate_onset():
    probs = {"onset": 0.4, "dry_spell": 0.3, "break": 0.2, "revival": 0.1}
    sig = _sig(rain_t=5.0, sum7=30.0, wet_streak=1, wet7=2)
    d = build_decision(probs, sig, crop_profile=PADDY)
    assert d.decision == "PREPARE"


def test_decision_irrigation_prepare_on_high_dry_spell_after_wet():
    probs = {"onset": 0.55, "dry_spell": 0.7, "break": 0.3, "revival": 0.2}
    sig = _sig(rain_t=8.0, sum7=70.0, wet_streak=3, wet7=4)
    d = build_decision(probs, sig, crop_profile=PADDY)
    assert d.decision == "IRRIGATION_PREPARE"


def test_decision_monitor_when_weak_signal():
    probs = {"onset": 0.2, "dry_spell": 0.3, "break": 0.2, "revival": 0.1}
    sig = _sig()
    d = build_decision(probs, sig, crop_profile=PADDY)
    assert d.decision == "MONITOR"


def test_decision_stays_deterministic_and_versioned():
    probs = {"onset": 0.7, "dry_spell": 0.2, "break": 0.15, "revival": 0.1}
    sig = _sig(rain_t=12.0, sum7=85.0, wet_streak=3, wet7=4)
    a = build_decision(probs, sig, crop_profile=PADDY)
    b = build_decision(probs, sig, crop_profile=PADDY)
    assert a == b
    assert a.thresholds_version == RULES["version"]
    assert a.as_dict()["decision"] == a.decision


def test_decision_requires_inputs():
    with pytest.raises(DecisionError):
        build_decision({}, {})
    with pytest.raises(DecisionError):
        build_decision({"onset": 0.7}, {})


# ---------------------------------------------------------------- advisory
def test_advisory_bilingual_and_printable():
    probs = {"onset": 0.25, "dry_spell": 0.7, "break": 0.2, "revival": 0.1}
    sig = _sig(rain_t=40.0, sum7=55.0, wet_streak=1, dry_streak=4, wet7=1)
    d = build_decision(probs, sig, crop_profile=PADDY)
    adv = generate_village_advisory(d, "2024-06-07", village_id="demo_001",
                                    village_name="Demo Agricultural Village",
                                    location_hint="10.75,77.5", crop="paddy")
    msg = adv.as_dict()
    assert msg["decision"] == "WAIT"
    assert "Tamil" or "ஊர்" in msg["messages"]["ta"]["title"]
    assert "VILLAGE:" in msg["messages"]["en"]["print_head"]
    assert msg["messages"]["en"]["block"], "english block non-empty"
    assert msg["messages"]["ta"]["block"].startswith(TA_DECISION["WAIT"]), \
        "Tamil block should open with the farmer-friendly WAIT phrase"


# ------------------------------------------------------------- delivery
def test_all_channels_generate_payloads():
    for ch in CHANNELS:
        payload = deliver(ch, "Some English advisory text.", "சில தமிழ் ஆலோசனை.",
                          "2024-06-07")
        assert payload["channel"] == ch
        assert payload["message"].strip()
        assert "MOCK" in payload["via"] or "MOCK" in payload["mock_notice"]


def test_unknown_channel_rejected():
    with pytest.raises(ValueError):
        deliver("carrier_pigeon", "en", "ta", "now")


def test_ivr_script_has_play_control():
    script = ivr_script("Wait", "சில தமிழ் ஆலோசனை.")
    assert "▶ PLAY ADVISORY" in script
    assert "Wait" in script


# ----------------------------------------------------------- config integrity
def test_profiles_load_and_sow_threshold_present():
    assert PADDY is not None
    assert PADDY["sow_confidence_needed"] == 0.6
    assert len(PROFILES) >= 3