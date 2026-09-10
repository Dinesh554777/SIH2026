"""Observation store: read-only access to the frozen Phase H feature matrix.

Supports historical/demo serving for a (cell_id, date). Real-time ingest is NOT part
of the MVP; the store keeps a per-cell chronological timeline so the persistence
previous-day state lookup matches the frozen baseline definition exactly.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.data_pipeline_utils import ROOT

PH_MATRIX = ROOT / "data" / "processed" / "phase_h_matrix.parquet"
PREDICTION_TARGET_COLS = {
    "onset": "onset_active",
    "break": "break_active",
    "revival": "revival_day",
    "dry_spell": "dry_spell_active",
}
SEASON_START = (6, 1)
SEASON_END = (9, 30)


def in_jjas(d: pd.Timestamp) -> bool:
    return (d.month, d.day) >= SEASON_START and (d.month, d.day) <= SEASON_END


class ObservationStore:
    def __init__(self, matrix: pd.DataFrame):
        self.matrix = matrix
        df = matrix.sort_values(["cell_id", "date"]).reset_index(drop=True)
        df["_ts"] = pd.to_datetime(df["date"])
        self.df = df
        self._groups: dict[str, np.ndarray] = {
            cid: np.asarray(g["_ts"].to_numpy(), dtype="datetime64[ns]")
            for cid, g in df.groupby("cell_id")
        }
        self._pos: dict[str, np.ndarray] = {
            cid: g.index.to_numpy() for cid, g in df.groupby("cell_id")
        }
        self._cells = sorted(df["cell_id"].unique().tolist())

    @classmethod
    def from_file(cls, path=PH_MATRIX) -> "ObservationStore":
        return cls(pd.read_parquet(path))

    @property
    def cell_ids(self) -> list[str]:
        return list(self._cells)

    def date_range(self, cell_id: str) -> tuple[pd.Timestamp, pd.Timestamp]:
        d = self._groups[cell_id]
        return pd.Timestamp(d[0]), pd.Timestamp(d[-1])

    def latest_date(self, cell_id: str) -> pd.Timestamp:
        return self.date_range(cell_id)[1]

    def timeline_years(self, cell_id: str) -> list[int]:
        lo, hi = self.date_range(cell_id)
        return list(range(int(lo.year), int(hi.year) + 1))

    def _locate(self, cell_id: str, date: pd.Timestamp) -> tuple[int, int] | None:
        dates = self._groups[cell_id]
        key = np.datetime64(date)
        i = int(np.searchsorted(dates, key))
        if 0 <= i < len(dates) and dates[i] == key:
            return int(self._pos[cell_id][i]), i
        return None

    def row(self, cell_id: str, date: pd.Timestamp) -> pd.Series | None:
        hit = self._locate(cell_id, date)
        if hit is None:
            return None
        pos, _ = hit
        return self.df.iloc[pos]

    def previous_day(self, cell_id: str, date: pd.Timestamp) -> pd.Series | None:
        hit = self._locate(cell_id, date)
        if hit is None:
            return None
        _, i = hit
        if i <= 0:
            return None
        prev_pos = int(self._pos[cell_id][i - 1])
        return self.df.iloc[prev_pos]

    def row_features(self, cell_id: str, date: pd.Timestamp, features: list[str]) -> pd.Series | None:
        r = self.row(cell_id, date)
        if r is None:
            return None
        return r[features]

    def data_completeness(self, row: pd.Series, features: list[str]) -> float:
        if row is None:
            return 0.0
        vals = row[features]
        present = vals.notna().sum()
        return float(present) / max(len(features), 1)


_DEFAULT: "ObservationStore | None" = None


def default_store(matrix: pd.DataFrame | None = None) -> "ObservationStore":
    global _DEFAULT
    if _DEFAULT is None:
        if matrix is None:
            matrix = pd.read_parquet(PH_MATRIX)
        _DEFAULT = ObservationStore(matrix)
    return _DEFAULT