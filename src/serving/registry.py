"""Pilot cell registry (read-only, derived from the Phase H matrix).

A cell is a 0.25-degree grid cell. Regions are bbox-derived groupings only
(see region_of in src.modeling.common); they are NOT official admin boundaries.
"""
from __future__ import annotations

import re

import pandas as pd

from src.data_pipeline_utils import ROOT
from src.modeling.common import region_of

CELL_ID_RE = re.compile(r"^\d{1,2}(?:\.\d+)?_\d{1,2}(?:\.\d+)?$")


def load_cells(matrix: pd.DataFrame) -> pd.DataFrame:
    cols = {"cell_id", "lat", "lon"}
    if "bbox_guess" in matrix.columns:
        cols.add("bbox_guess")
    cells = matrix[list(cols)].drop_duplicates()
    if "bbox_guess" in cells.columns:
        cells = cells.assign(region=cells["bbox_guess"].map(region_of))
        cells = cells.drop(columns=["bbox_guess"])
    else:
        cells = cells.assign(region="UNKNOWN")
    cells = cells.sort_values(["lat", "lon"]).reset_index(drop=True)
    return cells


class CellRegistry:
    def __init__(self, cells: pd.DataFrame):
        self.cells = cells
        self._by_id = {r["cell_id"]: r for _, r in cells.iterrows()}

    @classmethod
    def from_matrix(cls, matrix: pd.DataFrame) -> "CellRegistry":
        return cls(load_cells(matrix))

    @property
    def ids(self) -> list[str]:
        return list(self.cells["cell_id"])

    def get(self, cell_id: str) -> dict | None:
        row = self._by_id.get(cell_id)
        if row is None:
            return None
        return {
            "cell_id": row["cell_id"],
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "region": str(row["region"]),
            "admin_note": "grid_cell_only",
        }

    def summary(self) -> dict:
        return {
            "n_cells": int(len(self.cells)),
            "regions": sorted(self.cells["region"].dropna().unique().tolist()),
            "spatial_unit": {
                "type": "regular_grid_0.25deg",
                "note": "Pilot grid cell. Not an official village/block boundary.",
            },
            "cell_ids": self.ids,
        }

    @staticmethod
    def is_valid_id(cell_id: str) -> bool:
        return bool(CELL_ID_RE.match(cell_id))


_DEFAULT: "CellRegistry | None" = None


def default_registry(matrix: pd.DataFrame | None = None) -> "CellRegistry":
    global _DEFAULT
    if _DEFAULT is None:
        if matrix is None:
            matrix = pd.read_parquet(ROOT / "data" / "processed" / "phase_h_matrix.parquet")
        _DEFAULT = CellRegistry.from_matrix(matrix)
    return _DEFAULT