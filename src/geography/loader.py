"""GeoJSON boundary loader.

Reads authoritative administrative GeoJSON (WGS84, lon/lat degrees only) into
shapely polygons with hierarchy links. Deterministic: features are processed in
sorted (level, id) order; geometry reference is the feature's source record id.

Only polygons / multipolygons are accepted. Nothing is interpolated,
densified, or snapped -- the grid intersection uses the geometry as-is.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from src.geography.constants import GEOGRAPHY_TYPES, HIERARCHY
from src.geography.sources import SourceMetadata


class BoundaryError(ValueError):
    """Raised when a boundary bundle is structurally invalid (fail loud)."""


@dataclass(frozen=True)
class BoundaryPolygon:
    """One administrative polygon with its provenance attached."""

    geography_type: str
    geography_id: str
    name: str
    parent_geography_id: str | None
    geometry: BaseGeometry
    source: str
    version: str
    geometry_ref: str  # record id within the source file

    @property
    def latitude(self) -> float:
        return float(self.geometry.centroid.y)

    @property
    def longitude(self) -> float:
        return float(self.geometry.centroid.x)


_REQUIRED_PROPERTIES = ("level", "id", "name")


def _feature_record_id(src: Path, feature_index: int, props: dict) -> str:
    return f"{src.stem}:{props['id']}"


def load_boundaries(directory: Path, meta: SourceMetadata) -> list[BoundaryPolygon]:
    """Load every `*.geojson` in `directory` into a deterministic list."""
    files = sorted(directory.glob("*.geojson"))
    if not files:
        raise BoundaryError(f"no .geojson boundary files in {directory}")

    polygons: list[BoundaryPolygon] = []
    for path in files:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise BoundaryError(f"invalid GeoJSON in {path}: {exc}") from exc
        features = raw.get("features")
        if not isinstance(features, list):
            raise BoundaryError(f"GeoJSON {path} has no features list")

        for fi, feat in enumerate(sorted(features, key=lambda f: _props_key(f))):
            props = feat.get("properties") or {}
            missing = [k for k in _REQUIRED_PROPERTIES if k not in props]
            if missing:
                raise BoundaryError(
                    f"{path} feature {fi} missing properties {missing} (got {props})")
            level = str(props["level"])
            if level not in GEOGRAPHY_TYPES:
                raise BoundaryError(
                    f"{path} feature {fi} has invalid level {level!r} "
                    f"(expected one of {GEOGRAPHY_TYPES})")
            parent = props.get("parent_id")
            if level != "state" and not parent:
                raise BoundaryError(
                    f"{path} feature {fi} ({level}) must define parent_id")
            if level == "state" and parent is not None:
                raise BoundaryError(
                    f"{path} feature {fi} is a state but defines parent_id")
            try:
                geom = shape(feat.get("geometry") or {})
            except Exception as exc:
                raise BoundaryError(f"{path} feature {fi}: invalid geometry: {exc}")
            if geom.is_empty or not geom.is_valid:
                raise BoundaryError(f"{path} feature {fi}: empty/invalid geometry")
            if not _is_area_geometry(geom):
                raise BoundaryError(f"{path} feature {fi}: {geom.geom_type} is not "
                                    "a Polygon/MultiPolygon")
            polygons.append(BoundaryPolygon(
                geography_type=level,
                geography_id=str(props["id"]),
                name=str(props["name"]),
                parent_geography_id=str(parent) if parent is not None else None,
                geometry=geom,
                source=meta.dataset_name,
                version=meta.version,
                geometry_ref=_feature_record_id(path, fi, props),
            ))

    _validate_hierarchy(polygons)
    return _sorted(polygons)


def _props_key(feat: dict):
    props = feat.get("properties") or {}
    return (props.get("level", ""), str(props.get("id", "")))


def _is_area_geometry(geom: BaseGeometry) -> bool:
    return geom.geom_type in ("Polygon", "MultiPolygon")


def _sorted(polygons: list[BoundaryPolygon]) -> list[BoundaryPolygon]:
    return sorted(polygons, key=lambda p: (p.geography_type, p.geography_id))


def _validate_hierarchy(polygons: list[BoundaryPolygon]) -> None:
    """Fail loudly when a child references a non-existent parent at the same
    bundle level (prevents silent organization of unsupported boundaries)."""
    by_type: dict[str, set[str]] = {}
    for p in polygons:
        by_type.setdefault(p.geography_type, set()).add(p.geography_id)
    for p in polygons:
        if p.geography_type == "state":
            continue
        parent_type = HIERARCHY[p.geography_type]
        if parent_type not in by_type:
            # parent level not provided: allowed, mapping simply happens at the
            # finest provided level (documented behavior).
            continue
        if p.parent_geography_id not in by_type[parent_type]:
            raise BoundaryError(
                f"{p.geography_type} {p.geography_id} references unknown "
                f"parent {parent_type} {p.parent_geography_id!r}")