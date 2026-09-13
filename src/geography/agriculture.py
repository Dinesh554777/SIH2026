"""Agricultural metadata lookup (authoritative only).

Profiles live under `GEOGRAPHY_AGRI_DIR/<geography_id>.json`. A JSON file must
contain exactly keys from `AGRI_METADATA_FIELDS` plus optional `source`; any
unknown key is rejected (fail loud). Missing profile or missing data =>
`unavailable`. Values are never invented here.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.geography.constants import AGRI_METADATA_FIELDS, UNAVAILABLE
from src.geography.entities import AgricultureProfile


class AgricultureError(ValueError):
    """Raised on malformed authoritative agricultural metadata (fail loud)."""


def load_agriculture_profile(geography_type: str, geography_id: str,
                             agri_root: Path) -> AgricultureProfile:
    if not agri_root.is_dir():
        return AgricultureProfile.unavailable(geography_type, geography_id)
    path = agri_root / f"{geography_id}.json"
    if not path.is_file():
        return AgricultureProfile.unavailable(geography_type, geography_id)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AgricultureError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise AgricultureError(f"agriculture profile must be an object: {path}")

    allowed = set(AGRI_METADATA_FIELDS) | {"source"}
    unknown = [k for k in raw if k not in allowed]
    if unknown:
        raise AgricultureError(
            f"unknown agricultural field(s) {unknown} in {path}; allowed "
            f"fields are {AGRI_METADATA_FIELDS}")

    source_name = raw.get("source")
    if not source_name:
        raise AgricultureError(f"agriculture profile missing 'source' audit: {path}")
    fields = {k: v for k, v in raw.items() if k in AGRI_METADATA_FIELDS}
    for k, v in fields.items():
        if v is None or (isinstance(v, str) and not v.strip()):
            raise AgricultureError(f"agriculture field {k!r} empty in {path} "
                                   f"(use unavailable, never blank)")
    return AgricultureProfile(
        geography_type=geography_type,
        geography_id=geography_id,
        availability=UNAVAILABLE if not fields else "available",
        fields=fields,
        source=str(source_name),
    )