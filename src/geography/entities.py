"""Geography domain entities: administrative entity, grid->admin mapping,
agriculture profile. Pure data containers with stable, ordered records.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.geography.constants import GRID_CELL_TYPE, UNAVAILABLE


@dataclass(frozen=True)
class GeographyEntity:
    """One administrative entity (state/district/block/village).

    `geometry_ref` is a reference (e.g. the GeoJSON feature path / record id),
    never an inline geometry, so no boundary is copied into science code.
    """

    geography_type: str
    geography_id: str
    name: str
    parent_geography_id: str | None
    latitude: float | None
    longitude: float | None
    geometry_ref: str | None
    source: str
    source_version: str
    attributes: dict = field(default_factory=dict)

    def record(self) -> dict:
        return {
            "geography_type": self.geography_type,
            "geography_id": self.geography_id,
            "name": self.name,
            "parent_geography_id": self.parent_geography_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "geometry_ref": self.geometry_ref,
            "source": self.source,
            "source_version": self.source_version,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class GridToAdminMapping:
    """Deterministic area-weighted mapping of one grid cell into one
    administrative polygon (Product layer only).

    intersection_fraction = intersection_area / grid_cell_area, in [0, 1].
    """

    grid_cell_id: str
    geography_type: str
    geography_id: str
    intersection_fraction: float
    mapping_method: str
    source: str
    version: str
    cell_area_deg2: float
    intersection_area_deg2: float

    def record(self) -> dict:
        return {
            "grid_cell_id": self.grid_cell_id,
            "geography_type": self.geography_type,
            "geography_id": self.geography_id,
            "intersection_fraction": self.intersection_fraction,
            "mapping_method": self.mapping_method,
            "source": self.source,
            "version": self.version,
            "cell_area_deg2": self.cell_area_deg2,
            "intersection_area_deg2": self.intersection_area_deg2,
        }


@dataclass(frozen=True)
class AgricultureProfile:
    """Authoritative agricultural metadata for a geography entity.

    When no authoritative dataset exists for the entity, `availability` is
    `unavailable` and `fields` is empty -- values are never invented.
    """

    geography_type: str
    geography_id: str
    availability: str
    fields: dict = field(default_factory=dict)
    source: str | None = None

    @classmethod
    def unavailable(cls, geography_type: str, geography_id: str) -> "AgricultureProfile":
        return cls(
            geography_type=geography_type,
            geography_id=geography_id,
            availability=UNAVAILABLE,
        )

    def record(self) -> dict:
        return {
            "geography_type": self.geography_type,
            "geography_id": self.geography_id,
            "availability": self.availability,
            "fields": dict(self.fields),
            "source": self.source,
        }


def grid_cell_entity(cell: dict, source: str, source_version: str) -> GeographyEntity:
    """Product-layer grid-cell entity referencing the scientific cell registry.

    This is a *reference* to a scientific cell, not an administrative boundary.
    `cell` must contain cell_id, latitude, longitude. No geometry is invented.
    """
    return GeographyEntity(
        geography_type=GRID_CELL_TYPE,
        geography_id=str(cell["cell_id"]),
        name=f"grid {cell['cell_id']}",
        parent_geography_id=None,
        latitude=float(cell["latitude"]),
        longitude=float(cell["longitude"]),
        geometry_ref="cells.cell_id",
        source=source,
        source_version=source_version,
    )