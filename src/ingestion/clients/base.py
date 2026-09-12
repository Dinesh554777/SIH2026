"""Source abstraction for live observations (Gate J1).

A source returns a raw, source-specific response. All parsing is isolated inside
the client; the rest of the application only ever sees the normalized
Observation model (via the normalizer). Forecasting is decoupled from any
single provider by this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from src.ingestion.errors import ConfigurationError


@dataclass
class SourceResponse:
    """Raw source response before validation/normalization.

    rows: list[dict] with at least keys
          {lat, lon, observation_time (datetime), rainfall (mm/day)}
    metadata: source-specific bookkeeping (target date, coverage, version).
    """

    source: str
    rows: list[dict]
    retrieved_at: datetime
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.retrieved_at.tzinfo is None:
            raise ConfigurationError("retrieved_at must be timezone-aware")


class ObservationSource(ABC):
    """Interface every live observation provider implements.

    `is_mock` is True ONLY for deterministic test fixtures and MUST be False for
    every real provider; IngestionService refuses persisted mock data by default.
    """

    name: str = "unnamed"
    is_mock: bool = False

    @abstractmethod
    def fetch(self, now: datetime | None = None) -> SourceResponse:
        """Fetch the latest available observations for the pilot grid."""

    @abstractmethod
    def describe(self) -> dict:
        """Source identity + configuration (never secrets)."""