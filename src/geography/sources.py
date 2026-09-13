"""Authoritative GIS source registry.

A source is a folder under `GEOGRAPHY_SOURCES_DIR` that MUST contain a
`source.json` with the fields documented in §15 of the geography update.
Without it the source is refused (`unavailable`) -- boundaries are never
silently ingested.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.geography.constants import GEOGRAPHY_READY_DIR, SOURCE_META_FILE


class SourceError(ValueError):
    """Raised when an authoritative source is missing or invalid."""


@dataclass(frozen=True)
class SourceMetadata:
    """Recorded provenance for one authoritative boundary dataset."""

    dataset_name: str
    provider: str
    version: str
    release_date: str | None
    resolution: str | None
    license: str | None
    url: str | None
    crs: str
    geometry_quality: str | None

    @classmethod
    def from_file(cls, path: Path) -> "SourceMetadata":
        if not path.is_file():
            raise SourceError(f"missing source metadata file: {path}")
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise SourceError(f"invalid JSON in {path}: {exc}") from exc
        if not isinstance(raw, dict):
            raise SourceError(f"source metadata must be a JSON object: {path}")
        required = ("dataset_name", "provider", "version", "crs")
        missing = [k for k in required if not raw.get(k)]
        if missing:
            raise SourceError(f"source.json missing required keys {missing}: {path}")
        if not any(token in str(raw["crs"]).upper()
                   for token in ("4326", "WGS84", "EPSG:4326")):
            raise SourceError(
                f"unsupported CRS {raw['crs']!r} - only EPSG:4326 / WGS84 "
                f"(lon/lat degree) GeoJSON is accepted (no projection stack)")
        if not raw.get("url"):
            raise SourceError(f"source.json must record a download URL: {path}")
        return cls(
            dataset_name=str(raw["dataset_name"]),
            provider=str(raw["provider"]),
            version=str(raw["version"]),
            release_date=str(raw["release_date"]) if raw.get("release_date") else None,
            resolution=str(raw["resolution"]) if raw.get("resolution") else None,
            license=str(raw["license"]) if raw.get("license") else None,
            url=str(raw["url"]),
            crs=str(raw["crs"]),
            geometry_quality=str(raw["geometry_quality"]) if raw.get(
                "geometry_quality") else None,
        )


@dataclass(frozen=True)
class DiscoveredSource:
    directory: Path
    metadata: SourceMetadata


def discover_sources(source_root: Path) -> list[DiscoveredSource]:
    """Return valid, sorted authoritative sources under `source_root`.

    Folders without a valid source.json are SKIPPED and surfaced in
    `refused()` so the absence is explicit rather than silent.
    """
    if not source_root.is_dir():
        return []
    items = []
    for child in sorted(source_root.iterdir()):
        if not child.is_dir():
            continue
        try:
            meta = SourceMetadata.from_file(child / SOURCE_META_FILE)
        except SourceError:
            continue
        items.append(DiscoveredSource(directory=child, metadata=meta))
    return items


def refused_sources(source_root: Path) -> list[tuple[Path, str]]:
    """Folders under source_root that lack a valid source.json (explicit)."""
    if not source_root.is_dir():
        return []
    refused = []
    for child in sorted(source_root.iterdir()):
        if not child.is_dir():
            continue
        try:
            SourceMetadata.from_file(child / SOURCE_META_FILE)
        except SourceError as exc:
            refused.append((child, str(exc)))
    return refused


def ready_dir() -> Path:
    """Directory where the single *selected* validated boundary bundle lives.

    Only a bundle present here is used for mapping. The dir always exists so
    its absence is detectable and reported as `unavailable`.
    """
    GEOGRAPHY_READY_DIR.mkdir(parents=True, exist_ok=True)
    return GEOGRAPHY_READY_DIR