"""Geography / agricultural pilot package (Product layer).

The scientific layer (0.25-degree grid, frozen Phase H model) is never touched.
Administrative geography and grid->admin mapping are populated only from
authoritative GIS data registered under data/geography/sources/.
"""
from src.geography.entities import (AgricultureProfile, GeographyEntity,
                                    GridToAdminMapping)
from src.geography.registry import GeographyRegistry, load_grid_cells

__all__ = [
    "AgricultureProfile",
    "GeographyEntity",
    "GridToAdminMapping",
    "GeographyRegistry",
    "load_grid_cells",
]