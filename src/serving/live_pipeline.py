import os
from datetime import datetime, timezone
import threading
import pandas as pd

from src.ingestion.clients.imd import IMDGridSource
from src.ingestion.clients.mock import MockObservationSource
from src.ingestion.config import load_live_config
from src.ingestion.normalizer import CellMapper
from src.ingestion.service import IngestionService
from src.features.build_features import build_imd_features, add_imd_anomalies, train_climatology
from src.serving.store import ObservationStore
from src.serving.registry import default_registry

_ingest_lock = threading.Lock()
_cached_ingest_result = None
_cached_ingest_time = None

def get_live_row_and_metadata(cell_id: str, store: ObservationStore) -> tuple[pd.Series | None, dict]:
    global _cached_ingest_result, _cached_ingest_time
    cfg = load_live_config()
    cells = default_registry().cells
    mapper = CellMapper(cells)
    
    # Select source
    if cfg.live_data_source == "mock":
        source = MockObservationSource(cells)
    else:
        source = IMDGridSource(cells, url=cfg.source_url, timeout=cfg.request_timeout_seconds)
    
    svc = IngestionService(
        source, mapper,
        max_age_hours=cfg.max_observation_age_hours,
        future_tolerance_seconds=cfg.future_tolerance_seconds,
        max_retries=cfg.max_retries,
        allow_mock=cfg.allow_mock
    )
    
    now = datetime.now(timezone.utc)
    
    with _ingest_lock:
        if _cached_ingest_time and _cached_ingest_result and (now - _cached_ingest_time).total_seconds() < 300:
            res = _cached_ingest_result
        else:
            res = svc.ingest(now=now)
            _cached_ingest_result = res
            _cached_ingest_time = now
            
    metadata = {
        "mode": "live",
        "source": {
            "name": res.source,
            "status": "UNAVAILABLE" if res.status == "failed" else ("STALE" if res.freshness == "stale" else "ACTIVE"),
            "observed_at": res.observation_time.isoformat() if res.observation_time else None,
            "forecast_generated_at": now.isoformat(),
            "data_age_minutes": int((now - res.observation_time).total_seconds() / 60) if res.observation_time else None
        }
    }
    
    if res.status == "failed" or not res.observations:
        return None, metadata
        
    # Get observation for the requested cell_id
    obs = next((o for o in res.observations if o.cell_id == cell_id), None)
    if not obs:
        return None, metadata
        
    # ---------------- Feature Generation ----------------
    # We need to construct the features for today by appending today's rain to the historical context
    # Get last 60 days of historical data for this cell to compute rolling features
    history = store.df[store.df["cell_id"] == cell_id].sort_values("date").tail(60).copy()
    
    # We need to construct a dataframe in the format expected by build_imd_features (cell_id, date, rain)
    imd_df = pd.DataFrame({
        "cell_id": history["cell_id"],
        "date": history["date"],
        "rain": history["imd_rain_t"]
    })
    
    # Append the new live observation
    new_obs = pd.DataFrame({
        "cell_id": [cell_id],
        "date": [pd.Timestamp(obs.observation_time.date())],
        "rain": [obs.rainfall_mm]
    })
    
    imd_df = pd.concat([imd_df, new_obs], ignore_index=True)
    
    # Generate IMD features
    feat = build_imd_features(imd_df, cells)
    clim = train_climatology(imd_df, cells)
    feat = add_imd_anomalies(feat, clim)
    
    # Extract the last row (our new live row)
    live_features = feat.iloc[-1].copy()
    
    # Now we need to create the final row to pass to `predict()`.
    # It must contain ALL features that ModelService expects.
    # The XGBoost model uses `revival_features`. Let's take the last row of `history`,
    # which has the CHIRPS/NASA features, and update it with the new IMD features and new date.
    final_row = history.iloc[-1].copy()
    final_row["date"] = pd.Timestamp(obs.observation_time.date())
    final_row["_ts"] = pd.to_datetime(final_row["date"])
    
    # Update IMD features
    for col in feat.columns:
        if col not in ["date", "cell_id", "year", "doy"]:
            final_row[col] = live_features[col]
            
    return final_row, metadata
