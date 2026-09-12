"""PostgreSQL application database layer for Phase I-A.

Scientific data stays in Parquet; this package only persists application
records: locations, model provenance, forecasts, advisories.
"""
from src.database import config as config  # noqa: F401