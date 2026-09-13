"""Deterministic grid -> administrative mapping.

Scientific layer: 0.25-degree grid cells (frozen Phase H matrix).
Product layer : administrative polygons (authoritative GIS only).

Mapping method (default and only used method):
    `area_weighted_intersection` -- for each grid cell polygon, intersect with
    each administrative polygon and record intersection_area / cell_area as the
    intersection_fraction. No nearest-centroid assignment, no snapping, no
    interpolation. A cell is mapped to every polygon it overlaps.

The mapping is deterministic: results are fully sorted and never iterate over
a hash-ordered set, so identical input produces byte-identical output.
"""
from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import box

from src.geography.constants import (AREA_WEIGHTED, GRID_STEP_DEG,
                                     HIERARCHY)
from src.geography.entities import GridToAdminMapping
from src.geography.loader import BoundaryPolygon


class MappingError(ValueError):
    """Raised when the mapping inputs are inconsistent (fail loud)."""


@dataclass(frozen=True)
class CellBox:
    cell_id: str
    latitude: float
    longitude: float
    box: object  # shapely Polygon


def grid_cells_from_df(cells: "object") -> list[CellBox]:
    """Build 0.25-degree cell boxes from the frozen cells registry rows.

    Input rows must expose cell_id, lat, lon (the serving registry layout).
    """
    out: list[CellBox] = []
    for row in cells.itertuples(index=False):
        cid = str(row.cell_id)
        lat = float(row.lat)
        lon = float(row.lon)
        out.append(CellBox(
            cell_id=cid, latitude=lat, longitude=lon,
            box=box(lon - GRID_STEP_DEG / 2, lat - GRID_STEP_DEG / 2,
                    lon + GRID_STEP_DEG / 2, lat + GRID_STEP_DEG / 2)))
    return sorted(out, key=lambda c: c.cell_id)


def cell_area_deg2(cell: CellBox) -> float:
    return float(cell.box.area)


def _finest_level(types: set[str]) -> str:
    """Map at the finest administrative level present in the boundary bundle."""
    for level in ("village", "block", "district", "state"):
        if level in types:
            return level
    raise MappingError("no administrative boundary levels available")


def map_grid_to_admin(cells_df, boundaries: list[BoundaryPolygon],
                      source: str, version: str,
                      method: str = AREA_WEIGHTED) -> list[GridToAdminMapping]:
    """Deterministic area-weighted grid->admin mapping at the finest level
    present in `boundaries`.

    `cells_df` is the frozen matrix-derived cells frame (cell_id, lat, lon).
    Rows are emitted sorted by (geography_id, grid_cell_id).
    """
    if method != AREA_WEIGHTED:
        raise MappingError(f"unsupported mapping method {method!r} "
                           f"(only {AREA_WEIGHTED} is implemented/validated)")
    if not boundaries:
        raise MappingError("no boundaries provided to map against")

    cells = grid_cells_from_df(cells_df)
    by_type: dict[str, list[BoundaryPolygon]] = {}
    for p in boundaries:
        by_type.setdefault(p.geography_type, []).append(p)
    finest = _finest_level(set(by_type))

    polys = sorted(by_type[finest], key=lambda p: p.geography_id)
    maps: list[GridToAdminMapping] = []
    for cell in cells:
        area = cell_area_deg2(cell)
        for p in polys:
            inter = cell.box.intersection(p.geometry)
            if inter.is_empty:
                continue
            ia = float(inter.area)
            frac = ia / area if area > 0 else 0.0
            if frac <= 0:
                continue
            maps.append(GridToAdminMapping(
                grid_cell_id=cell.cell_id,
                geography_type=p.geography_type,
                geography_id=p.geography_id,
                intersection_fraction=frac,
                mapping_method=method,
                source=source,
                version=version,
                cell_area_deg2=area,
                intersection_area_deg2=ia,
            ))
    return sorted(maps, key=lambda m: (m.geography_id, m.grid_cell_id))


def coverage_report(mappings: list[GridToAdminMapping],
                    cells_df) -> dict:
    """Per-cell coverage integrity: fraction of each cell covered by mapped
    polygons (used to surface unmapped/under-mapped cells -- never fabricate)."""
    cells = grid_cells_from_df(cells_df)
    per_cell: dict[str, float] = {c.cell_id: 0.0 for c in cells}
    for m in mappings:
        per_cell[m.grid_cell_id] = per_cell.get(m.grid_cell_id, 0.0) + m.intersection_fraction
    unmapped = [cid for cid, f in sorted(per_cell.items()) if f <= 0.0]
    partial = [cid for cid, f in sorted(per_cell.items())
               if 0.0 < f < 1.0 - 1e-9]
    return {
        "n_cells": len(cells),
        "n_mapped_cells": sum(1 for f in per_cell.values() if f > 0.0),
        "n_unmapped_cells": len(unmapped),
        "unmapped_cells": unmapped,
        "n_partial_cells": len(partial),
        "partial_cells": partial,
    }


def validate_parent_links(boundaries: list[BoundaryPolygon],
                          mappings: list[GridToAdminMapping]) -> None:
    """Fail loudly when mapped geography violates the parent hierarchy."""
    ids_by_type = {"state": set(), "district": set(), "block": set(),
                   "village": set()}
    parents = {}
    for p in boundaries:
        ids_by_type[p.geography_type].add(p.geography_id)
        parents[p.geography_id] = p.parent_geography_id
    H = HIERARCHY
    for m in mappings:
        gid = m.geography_id
        if m.geography_type not in ids_by_type:
            raise MappingError(f"mapped {m.geography_type} {gid} absent from boundaries")
        parent_id = parents.get(gid)
        parent_type = H.get(m.geography_type)
        if parent_type is not None and parent_id is not None:
            if parent_type in ids_by_type and parent_id not in ids_by_type[parent_type]:
                raise MappingError(f"{m.geography_type} {gid} has dangling parent {parent_id}")