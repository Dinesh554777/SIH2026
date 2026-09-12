"""Live observation ingestion + persistence (Gates J1 + J2).

Normalized live-observation pipeline:

    Live data source
         |  SourceClient.fetch(now)
         v
    SourceResponse  (raw rows + metadata)
         |  validators + normalizer
         v
    Observation[] (valid) / rejected[] (with quality + reason)
         |  IngestionPipeline (J2): PostgreSQL persistence + run status
         v
    ingestion_runs (SUCCESS/PARTIAL/BLOCKED/FAILED) + observations

J1/J2 perform NO forecasting, NO model inference and NO feature engineering
(that is Gate J3). Historical IMD files under data/raw/imd are historical
validation fixtures and are NEVER used as a live source.
"""

from src.ingestion.config import LiveConfig, load_live_config  # noqa: F401
from src.ingestion.errors import (ConfigurationError,  # noqa: F401
                                  SourceResponseError, SourceUnavailableError,
                                  ValidationError)
from src.ingestion.models import IngestionResult, Observation  # noqa: F401
from src.ingestion.service import IngestionService  # noqa: F401
from src.ingestion.normalizer import CellMapper, normalize_batch  # noqa: F401


def __getattr__(name: str):
    """Lazy exports that depend on src.database (avoid import cycles):
    `from src.ingestion import IngestionPipeline` works without executing the
    database model layer at package-import time."""
    if name in {"IngestionPipeline", "run_pipeline_once"}:
        from src.ingestion.pipeline import (IngestionPipeline,
                                            run_pipeline_once)
        return {"IngestionPipeline": IngestionPipeline,
                "run_pipeline_once": run_pipeline_once}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "LiveConfig", "load_live_config",
    "ConfigurationError", "SourceResponseError", "SourceUnavailableError", "ValidationError",
    "IngestionResult", "Observation",
    "IngestionService", "CellMapper", "normalize_batch",
    "IngestionPipeline", "run_pipeline_once",
]