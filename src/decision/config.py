"""Load and validate configurable decision thresholds + crop profiles.

Config files: data/decision/decision_rules.json and data/decision/crop_profiles.json.
Path can be overridden with the environment variable SIH_DECISION_RULES. The rules
files are the single source of truth for every threshold the decision engine uses.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

_DEFAULT_RULES = Path("data/decision/decision_rules.json")
_DEFAULT_PROFILES = Path("data/decision/crop_profiles.json")

_REQUIRED_RULES = {
    "targets": {
        "onset": ("moderate", "strong"),
        "dry_spell": ("elevated", "high"),
        "break": ("high",),
        "revival": ("moderate",),
    },
    "false_onset": (
        "elevated_rain_mm", "sustained_wet_days", "wet_days7_needed",
        "escalation_dry_streak"),
    "decision_priority": (),
}


def _load_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Decision config not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _validate_rules(cfg: dict) -> None:
    version = cfg.get("version")
    if not version:
        raise ValueError("decision_rules.json must declare a 'version'")
    targets = cfg.get("targets")
    if not isinstance(targets, dict):
        raise ValueError("decision_rules.json 'targets' missing")
    for target, keys in _REQUIRED_RULES["targets"].items():
        block = targets.get(target)
        if not isinstance(block, dict):
            raise ValueError(f"decision_rules.json: targets['{target}'] missing")
        for key in keys:
            if not isinstance(block.get(key), (int, float)):
                raise ValueError(
                    f"decision_rules.json: targets['{target}']['{key}'] must be a number")
    for key in _REQUIRED_RULES["false_onset"]:
        if not isinstance(cfg.get("false_onset", {}).get(key), (int, float)):
            raise ValueError(f"decision_rules.json: false_onset['{key}'] must be a number")
    priority = cfg.get("decision_priority")
    if not isinstance(priority, list) or not priority:
        raise ValueError("decision_rules.json: decision_priority must be a non-empty list")


def load_rules(path: str | os.PathLike | None = None) -> dict:
    p = Path(path) if path else Path(os.environ.get("SIH_DECISION_RULES", _DEFAULT_RULES))
    cfg = _load_json(p)
    _validate_rules(cfg)
    return cfg


def load_profiles(path: str | os.PathLike | None = None) -> list[dict]:
    p = Path(path) if path else Path(os.environ.get("SIH_CROP_PROFILES", _DEFAULT_PROFILES))
    data = _load_json(p)
    profiles = data.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("crop_profiles.json must define a non-empty 'profiles' list")
    return profiles


def find_profile(profiles: list[dict], crop: str | None = None, season: str | None = None) -> dict | None:
    for prof in profiles:
        if season and prof.get("season") != season:
            continue
        if crop and prof.get("crop") != crop:
            continue
        return prof
    if crop and season:
        return find_profile(profiles, crop=crop, season=None)
    return profiles[0] if profiles else None