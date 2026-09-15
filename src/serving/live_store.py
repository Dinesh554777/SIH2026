import pandas as pd
from src.serving.store import ObservationStore

class LiveObservationStore(ObservationStore):
    """A thread-safe request-scoped wrapper around the base ObservationStore 
    that injects a live row for a specific cell and date, without mutating global state."""
    
    def __init__(self, base: ObservationStore, cell_id: str, live_ts: pd.Timestamp, live_row: pd.Series):
        # We don't call super().__init__ because we don't want to rebuild indexes.
        # We just delegate to `base` for everything except the live row.
        self.base = base
        self.matrix = base.matrix
        self.df = base.df
        
        self.live_cell_id = cell_id
        self.live_ts = live_ts
        self.live_row = live_row
        
    @property
    def cell_ids(self) -> list[str]:
        return self.base.cell_ids
        
    def date_range(self, cell_id: str) -> tuple[pd.Timestamp, pd.Timestamp]:
        if cell_id == self.live_cell_id:
            return self.base.date_range(cell_id)[0], self.live_ts
        return self.base.date_range(cell_id)
        
    def latest_date(self, cell_id: str) -> pd.Timestamp:
        if cell_id == self.live_cell_id:
            return self.live_ts
        return self.base.latest_date(cell_id)
        
    def timeline_years(self, cell_id: str) -> list[int]:
        years = self.base.timeline_years(cell_id)
        if cell_id == self.live_cell_id and self.live_ts.year not in years:
            years.append(self.live_ts.year)
        return years
        
    def row(self, cell_id: str, date: pd.Timestamp) -> pd.Series | None:
        if cell_id == self.live_cell_id and date == self.live_ts:
            return self.live_row
        return self.base.row(cell_id, date)
        
    def previous_day(self, cell_id: str, date: pd.Timestamp) -> pd.Series | None:
        if cell_id == self.live_cell_id and date == self.live_ts:
            # The previous day relative to our live row is the latest historical row
            return self.base.row(cell_id, self.base.latest_date(cell_id))
        return self.base.previous_day(cell_id, date)
        
    def row_features(self, cell_id: str, date: pd.Timestamp, features: list[str]) -> pd.Series | None:
        r = self.row(cell_id, date)
        if r is None:
            return None
        return r[features]
        
    def data_completeness(self, row: pd.Series, features: list[str]) -> float:
        return self.base.data_completeness(row, features)

