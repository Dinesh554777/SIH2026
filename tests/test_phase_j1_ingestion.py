"""Gate J1 — Live Ingestion tests (no Internet access required).

Covers: configuration, source clients, per-observation validation, freshness
classification, normalization, deterministic geographic cell mapping, bounded
retry behavior, and the MOCK / TEST-ONLY source guard.

All tests are self-contained: pilot cells are built from a tiny synthetic grid
so nothing needs the 80 MB matrix or the network.
"""
from __future__ import annotations

import os
import sys
from datetime import date as date_t, datetime, timedelta, timezone

import pandas as pd
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ingestion.clients.base import ObservationSource, SourceResponse
from src.ingestion.clients.imd import (DEFAULT_IMD_POST_URL, IMDGridSource)
from src.ingestion.clients.mock import MockObservationSource
from src.ingestion.config import load_live_config
from src.ingestion.errors import (ConfigurationError, SourceResponseError,
                                  SourceUnavailableError, ValidationError)
from src.ingestion.models import (FRESHNESS_FRESH, FRESHNESS_FUTURE,
                                  FRESHNESS_STALE, IngestionResult,
                                  QUALITY_FUTURE, QUALITY_INVALID, QUALITY_MISSING,
                                  QUALITY_STALE, QUALITY_VALID)
from src.ingestion.normalizer import CellMapper, normalize_batch
from src.ingestion.service import IngestionService
from src.ingestion.validators import target_observation_date

NOW = datetime(2026, 9, 12, 12, 0, tzinfo=timezone.utc)

_LATS = [10.0, 10.25, 10.5]
_LONS = [76.25, 76.5, 76.75]


def build_cells() -> pd.DataFrame:
    rows = []
    for lat in _LATS:
        for lon in _LONS:
            rows.append({"cell_id": f"{lat:.2f}_{lon:.2f}", "lat": lat, "lon": lon})
    return pd.DataFrame(rows)


def raw_row(lat=10.0, lon=76.25, rain=12.5, cell_id="10.00_76.25",
            t=None) -> dict:
    return {
        "cell_id": cell_id,
        "lat": lat,
        "lon": lon,
        "observation_time": t or (NOW - timedelta(hours=1)),
        "rainfall": rain,
    }


@pytest.fixture(scope="module")
def mapper() -> CellMapper:
    return CellMapper(build_cells())


@pytest.fixture(scope="module")
def cells() -> pd.DataFrame:
    return build_cells()


# --------------------------------------------------------------------------- config
class TestConfig:
    def test_defaults_are_historical(self):
        cfg = load_live_config({})
        assert cfg.forecast_mode == "historical"
        assert cfg.live_data_source == "imd"
        assert cfg.max_retries == 2
        assert cfg.max_observation_age_hours == 48.0
        assert cfg.allow_mock is False

    def test_live_mode_accepted(self):
        cfg = load_live_config({"FORECAST_MODE": "live"})
        assert cfg.forecast_mode == "live"

    def test_invalid_mode_rejected(self):
        with pytest.raises(ConfigurationError):
            load_live_config({"FORECAST_MODE": "boom"})

    def test_invalid_source_rejected(self):
        with pytest.raises(ConfigurationError):
            load_live_config({"LIVE_DATA_SOURCE": "wunderground"})

    def test_mock_requires_allow_mock(self):
        with pytest.raises(ConfigurationError):
            load_live_config({"LIVE_DATA_SOURCE": "mock"})
        cfg = load_live_config({"LIVE_DATA_SOURCE": "mock", "LIVE_ALLOW_MOCK": "1"})
        assert cfg.live_data_source == "mock" and cfg.allow_mock

    def test_local_path_source_url_rejected(self):
        with pytest.raises(ConfigurationError):
            load_live_config({"LIVE_SOURCE_URL": "data/raw/imd/ind2015_rfp25.nc"})

    def test_bad_retries_rejected(self):
        with pytest.raises(ConfigurationError):
            load_live_config({"LIVE_MAX_RETRIES": "11"})


# --------------------------------------------------------------------------- imd client shape
class TestIMDClientShape:
    def test_default_url_is_verified_post_endpoint(self, cells):
        src = IMDGridSource(cells)
        assert src.post_url == DEFAULT_IMD_POST_URL
        assert src.is_mock is False
        d = src.describe()
        assert d["is_mock"] is False and "mm/day" in d["units"]

    def test_local_url_rejected(self, cells):
        with pytest.raises(ConfigurationError):
            IMDGridSource(cells, url="data/raw/imd/ind2015_rfp25.nc")

    def test_http_url_accepted(self, cells):
        src = IMDGridSource(cells, url="https://example.in/imd/rain.nc")
        assert src.post_url == "https://example.in/imd/rain.nc"


# --------------------------------------------------------------------------- validation
class TestValidation:
    def test_missing_required_field_rejected(self, mapper):
        rows = [{"lat": 10.0, "lon": 76.25}]  # no rainfall / time
        valid, rejected, _ = normalize_batch(rows, "t", NOW, mapper, NOW, 48.0, 3600.0)
        assert valid == [] and len(rejected) == 1
        assert rejected[0].quality_flag == QUALITY_INVALID
        assert "missing required field" in rejected[0].reason

    def test_negative_rainfall_rejected_not_zeroed(self, mapper):
        rows = [raw_row(rain=-3.0)]
        valid, rejected, _ = normalize_batch(rows, "t", NOW, mapper, NOW, 48.0, 3600.0)
        assert valid == []
        assert rejected[0].quality_flag == QUALITY_INVALID
        assert "negative" in rejected[0].reason

    def test_nan_rainfall_rejected(self, mapper):
        rows = [raw_row(rain=float("nan"))]
        _, rejected, _ = normalize_batch(rows, "t", NOW, mapper, NOW, 48.0, 3600.0)
        assert rejected and rejected[0].quality_flag == QUALITY_INVALID
        assert "not finite" in rejected[0].reason

    def test_missing_rainfall_is_missing_not_zero(self, mapper):
        rows = [raw_row(rain=None)]
        _, rejected, _ = normalize_batch(rows, "t", NOW, mapper, NOW, 48.0, 3600.0)
        assert rejected and rejected[0].quality_flag == QUALITY_MISSING

    def test_out_of_range_coordinates_rejected(self, mapper):
        rows = [raw_row(lat=95.0, lon=76.25)]
        _, rejected, _ = normalize_batch(rows, "t", NOW, mapper, NOW, 48.0, 3600.0)
        assert rejected and rejected[0].quality_flag == QUALITY_INVALID
        assert "latitude" in rejected[0].reason

    def test_naive_datetime_rejected(self, mapper):
        rows = [raw_row(t=datetime(2026, 9, 12, 6, 0))]
        _, rejected, _ = normalize_batch(rows, "t", NOW, mapper, NOW, 48.0, 3600.0)
        assert rejected and rejected[0].quality_flag == QUALITY_INVALID
        assert "timezone-aware" in rejected[0].reason

    def test_future_timestamp_rejected(self, mapper):
        rows = [raw_row(t=NOW + timedelta(hours=24))]
        _, rejected, _ = normalize_batch(rows, "t", NOW, mapper, NOW, 48.0, 3600.0)
        assert rejected and rejected[0].quality_flag == QUALITY_FUTURE

    def test_stale_timestamp_rejected(self, mapper):
        rows = [raw_row(t=NOW - timedelta(hours=200))]
        _, rejected, _ = normalize_batch(rows, "t", NOW, mapper, NOW, 48.0, 3600.0)
        assert rejected and rejected[0].quality_flag == QUALITY_STALE


# --------------------------------------------------------------------------- freshness
class TestFreshness:
    def test_fresh(self, mapper):
        rows = [raw_row(t=NOW - timedelta(hours=1))]
        valid, _, _ = normalize_batch(rows, "t", NOW, mapper, NOW, 48.0, 3600.0)
        assert valid and valid[0].quality_flag == QUALITY_VALID
        assert valid[0].observation_time.tzinfo is not None

    def test_classify_fresh(self, cells, mapper):
        src = MockObservationSource(cells)
        svc = IngestionService(src, mapper, allow_mock=True)
        assert svc.ingest(now=NOW).freshness == FRESHNESS_FRESH

    def test_classify_stale(self, cells, mapper):
        old = date_t(2026, 8, 1)
        src = MockObservationSource(cells, observation_date=old)
        svc = IngestionService(src, mapper, allow_mock=True, max_age_hours=6.0)
        assert svc.ingest(now=NOW).freshness == FRESHNESS_STALE

    def test_classify_future(self, cells, mapper):
        class _FutureSource(ObservationSource):
            is_mock = True
            name = "future-src"

            def __init__(self, cells_):
                self.cells = cells_

            def fetch(self, now=None):
                t = now or NOW
                rows = [raw_row(t=t + timedelta(hours=2))]
                return SourceResponse(source=self.name, rows=rows, retrieved_at=t)

            def describe(self):
                return {"name": self.name}

        svc = IngestionService(_FutureSource(cells), mapper, allow_mock=True)
        res = svc.ingest(now=NOW)
        assert res.freshness == FRESHNESS_FUTURE
        assert res.rejected and res.rejected[0].quality_flag == QUALITY_FUTURE


# --------------------------------------------------------------------------- normalization
class TestNormalization:
    def test_units_and_timestamps(self, cells, mapper):
        rows = [raw_row(), raw_row(lat=10.25, lon=76.5, rain=0.4, cell_id="10.25_76.50")]
        valid, rejected, _ = normalize_batch(rows, "imd", NOW, mapper, NOW, 48.0, 3600.0)
        assert len(valid) == 2 and rejected == []
        for o in valid:
            assert o.rainfall_mm >= 0.0
            assert o.observation_time.tzinfo is not None
            assert o.retrieved_at.tzinfo is not None
            assert o.source == "imd"
            assert o.quality_flag == QUALITY_VALID

    def test_iso_string_timestamp_accepted(self, mapper):
        rows = [raw_row(t="2026-09-12T10:00:00+00:00")]
        valid, _, _ = normalize_batch(rows, "t", NOW, mapper, NOW, 48.0, 3600.0)
        assert valid and valid[0].observation_time.tzinfo is not None


# --------------------------------------------------------------------------- geographic mapping
class TestCellMapping:
    def test_center_maps_exactly(self, mapper):
        assert mapper.resolve(10.25, 76.5) == ("10.25_76.50", None)

    def test_within_half_step_maps(self, mapper):
        cell_id, reason = mapper.resolve(10.12, 76.5)
        assert reason is None
        assert cell_id in ("10.00_76.50", "10.25_76.50")

    def test_far_away_rejected(self, mapper):
        cell_id, reason = mapper.resolve(22.0, 79.0)
        assert cell_id is None and "not within" in reason

    def test_cell_id_format_consistent(self, mapper):
        cell_id, _ = mapper.resolve(10.0, 76.25)
        assert cell_id.startswith("10.00_76.")


# --------------------------------------------------------------------------- retry
class _FlakySource(ObservationSource):
    name = "flaky"
    is_mock = True

    def __init__(self, rows_factory, fail_before_ok: int = 0, always_fail: bool = False):
        self._rows = rows_factory
        self._fail_before_ok = fail_before_ok
        self._always_fail = always_fail
        self.attempts = 0

    def fetch(self, now=None):
        self.attempts += 1
        if self._always_fail or self.attempts <= self._fail_before_ok:
            raise SourceUnavailableError("connection refused (simulated)")
        return SourceResponse(source=self.name, rows=self._rows(), retrieved_at=now or NOW)

    def describe(self):
        return {"name": self.name}


class TestRetry:
    def test_bounded_retries_then_clean_failure(self, mapper, cells):
        src = _FlakySource(lambda: [raw_row()], always_fail=True)
        svc = IngestionService(src, mapper, max_retries=2, allow_mock=True)
        res = svc.ingest(now=NOW)
        assert src.attempts == 3  # bounded, not infinite
        assert res.status == "failed"
        assert any("connection refused" in e for e in res.errors)

    def test_transient_then_success(self, mapper, cells):
        src = _FlakySource(lambda: [raw_row()], fail_before_ok=2)
        svc = IngestionService(src, mapper, max_retries=3, allow_mock=True)
        res = svc.ingest(now=NOW)
        assert res.status == "success" and res.rows_valid == 1
        assert src.attempts == 3

    def test_validation_error_not_retried(self, mapper):
        class BadSource(ObservationSource):
            name = "bad"
            is_mock = True

            def __init__(self):
                self.attempts = 0

            def fetch(self, now=None):
                self.attempts += 1
                raise ValidationError("client semantics broken")

            def describe(self):
                return {"name": self.name}

        src = BadSource()
        svc = IngestionService(src, mapper, max_retries=2, allow_mock=True)
        with pytest.raises(ValidationError):
            svc._fetch_with_retry(NOW)
        assert src.attempts == 1


# --------------------------------------------------------------------------- mock source
class TestMockSource:
    def test_deterministic(self, cells):
        a = MockObservationSource(cells).fetch(now=NOW)
        b = MockObservationSource(cells).fetch(now=NOW)
        assert a.rows == b.rows
        assert len(a.rows) == 9
        assert all("rainfall" in r and "observation_time" in r for r in a.rows)
        assert a.metadata["mock"] is True

    def test_nguard_mock_blocked_by_default(self, cells, mapper):
        src = MockObservationSource(cells)
        svc = IngestionService(src, mapper, allow_mock=False)
        res = svc.ingest(now=NOW)
        assert res.status == "failed"
        assert any("MOCK" in e for e in res.errors)

    def test_mock_allowed_explicitly(self, cells, mapper):
        src = MockObservationSource(cells)
        svc = IngestionService(src, mapper, allow_mock=True)
        res = svc.ingest(now=NOW)
        assert res.status == "success" and res.rows_valid == 9
        assert res.freshness == FRESHNESS_FRESH

    def test_mock_result_shape(self, cells, mapper):
        svc = IngestionService(MockObservationSource(cells), mapper, allow_mock=True)
        res = svc.ingest(now=NOW)
        assert isinstance(res, IngestionResult)
        d = res.as_dict()
        assert d["rows_valid"] == 9 and d["rows_rejected"] == 0
        assert res.observations[0].source == "mock-sim"


# --------------------------------------------------------------------------- target day helper
class TestHelpers:
    def test_target_observation_date_is_last_completed_day(self):
        assert target_observation_date(NOW) == NOW.date() - timedelta(days=1)