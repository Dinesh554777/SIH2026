"""Geography registry (config-driven, science-safe).

Loads ONLY from a validated "ready" boundary bundle under
`GEOGRAPHY_READY_DIR` (a bundle is authoritative only when it carries a valid
`source.json` plus GeoJSON). Without one, every administrative level reports
`unavailable` and the product simply continues on the 0.25-degree scientific
grid -- boundaries are never invented.

Grid cells always come from the frozen Phase H matrix (serving registry), i.e.
the scientific layer is untouched by anything in this module.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.geography.agriculture import (AgricultureError,
                                       load_agriculture_profile)
from src.geography.constants import (GEOGRAPHY_AGRI_DIR, GEOGRAPHY_READY_DIR,
                                     GEOGRAPHY_SOURCES_DIR, GEOGRAPHY_TYPES,
                                     HIERARCHY)
from src.geography.entities import GeographyEntity
from src.geography.loader import load_boundaries
from src.geography.mapper import coverage_report, map_grid_to_admin
from src.geography.sources import (SourceError, SourceMetadata,
                                   discover_sources, refused_sources)
from src.serving.registry import default_registry


def load_grid_cells(cells: pd.DataFrame | None = None) -> pd.DataFrame:
    return default_registry(cells).cells


class GeographyRegistry:
    """Deterministic administrative-geography view.

    `source_root` : raw authoritative source folders (only used for discovery
                    and provenance reporting).
    `ready_root`  : the single validated bundle actually consumed for mapping.
    """

    def __init__(self, source_root: Path | None = None,
                 ready_root: Path | None = None,
                 agri_root: Path | None = None,
                 cells: pd.DataFrame | None = None):
        self.source_root = Path(source_root) if source_root else GEOGRAPHY_SOURCES_DIR
        self.ready_root = Path(ready_root) if ready_root else GEOGRAPHY_READY_DIR
        self.agri_root = Path(agri_root) if agri_root else GEOGRAPHY_AGRI_DIR
        self.cells = load_grid_cells(cells)

        self.sources = discover_sources(self.source_root)
        self.refused = refused_sources(self.source_root)

        self.meta: SourceMetadata | None = None
        self.boundaries = []
        self._available_types: set[str] = set()
        self._load_ready()

    # ------------------------------------------------------------------ load
    def _load_ready(self) -> None:
        meta_path = self.ready_root / "source.json"
        if not meta_path.is_file():
            return
        try:
            meta = SourceMetadata.from_file(meta_path)
        except SourceError:
            return
        try:
            polys = load_boundaries(self.ready_root, meta)
        except Exception:
            polys = []  # invalid ready bundle -> refuse import (no boundaries)
        if not polys:
            return
        self.meta = meta
        self.boundaries = polys
        self._available_types = {p.geography_type for p in polys}

    @property
    def boundaries_available(self) -> bool:
        return self.meta is not None

    def unavailable_reason(self) -> str:
        if self.boundaries_available:
            return ""
        if self.refused:
            return ("no validated boundary bundle; refused sources = "
                    + str([(str(d), e) for d, e in self.refused]))
        return ("no authoritative GIS boundary data present (see "
                "reports/GEOGRAPHY_AGRICULTURE_UPDATE.md); administrative "
                "levels are unavailable by design")

    # -------------------------------------------------------------- entities
    def _entities(self, level: str, parent_id: str | None = None) -> list[dict]:
        if not self.boundaries_available or level not in self._available_types:
            return []
        out = []
        for p in self.boundaries:
            if p.geography_type != level:
                continue
            if parent_id is not None and p.parent_geography_id != parent_id:
                continue
            out.append(GeographyEntity(
                geography_type=level,
                geography_id=p.geography_id,
                name=p.name,
                parent_geography_id=p.parent_geography_id,
                latitude=p.latitude,
                longitude=p.longitude,
                geometry_ref=p.geometry_ref,
                source=p.source,
                source_version=p.version,
            ).record())
        return out

    def states(self) -> list[dict]:
        return self._entities("state")

    def districts(self, state_id: str | None = None) -> list[dict]:
        return self._entities("district", parent_id=state_id)

    def blocks(self, district_id: str | None = None) -> list[dict]:
        return self._entities("block", parent_id=district_id)

    def villages(self, block_id: str | None = None) -> list[dict]:
        return self._entities("village", parent_id=block_id)

    def children(self, geography_type: str, geography_id: str) -> list[dict]:
        if geography_type == "grid_cell":
            return []
        child_level = next((lvl for lvl, parent in HIERARCHY.items()
                            if parent == geography_type), None)
        if child_level is None or child_level not in self._available_types:
            return []
        return self._entities(child_level, parent_id=geography_id)

    # --------------------------------------------------------------- mapping
    def mappings(self) -> list[dict]:
        if not self.boundaries_available:
            return []
        maps = map_grid_to_admin(self.cells, self.boundaries,
                                 source=self.meta.dataset_name,
                                 version=self.meta.version)
        return [m.record() for m in maps]

    def coverage(self) -> dict:
        if not self.boundaries_available:
            return {"n_cells": int(len(self.cells)), "status": "unavailable"}
        maps = map_grid_to_admin(self.cells, self.boundaries,
                                 source=self.meta.dataset_name,
                                 version=self.meta.version)
        rep = coverage_report(maps, self.cells)
        rep["status"] = "available"
        return rep

    # -------------------------------------------------------------- metadata
    def agriculture(self, geography_type: str, geography_id: str) -> dict:
        try:
            profile = load_agriculture_profile(geography_type, geography_id,
                                               self.agri_root)
        except AgricultureError:
            raise
        return profile.record()

    def grid_cells(self) -> list[dict]:
        out = []
        for row in self.cells.itertuples(index=False):
            out.append({
                "grid_cell_id": str(row.cell_id),
                "latitude": float(row.lat),
                "longitude": float(row.lon),
                "region": str(getattr(row, "region", "UNKNOWN")),
                "note": "scientific 0.25-degree grid cell (model layer)",
            })
        return sorted(out, key=lambda c: c["grid_cell_id"])

    @property
    def n_grid_cells(self) -> int:
        return int(len(self.cells))

    # ---------------------------------------------------------------- summary
    def availability(self) -> dict:
        levels = {level: ("available" if (self.boundaries_available
                                          and level in self._available_types)
                          else "unavailable")
                  for level in GEOGRAPHY_TYPES}
        return {
            "status": ("available" if self.boundaries_available
                       else "unavailable"),
            "levels": levels,
            "reason": self.unavailable_reason(),
        }

    def summary(self) -> dict:
        return {
            "grid": {
                "n_cells": self.n_grid_cells,
                "source": "frozen phase_h_matrix.parquet (serving registry)",
            },
            "administrative": self.availability(),
            "sources": [{
                "dataset_name": s.metadata.dataset_name,
                "provider": s.metadata.provider,
                "version": s.metadata.version,
                "crs": s.metadata.crs,
                "license": s.metadata.license,
                "url": s.metadata.url,
                "directory": str(s.directory),
            } for s in self.sources],
            "refused": [{"directory": str(d), "error": e}
                        for d, e in self.refused],
        }