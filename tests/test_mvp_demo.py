"""Demo reproducibility test: the MVP_DEMO_SCENARIO contract must hold on every run."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.serving.demo import EXPECTED_REVIVAL_2024_08_12, DEMO_CELL, PIVOT_DATES
from src.serving.models import ModelService
from src.serving.rules import build_cards_with_bands
from src.serving.store import ObservationStore


@pytest.fixture(scope="module")
def service():
    store = ObservationStore.from_file()
    return ModelService(store, matrix=store.matrix)


def test_demo_anchor_value(service):
    p = service.predict(DEMO_CELL, pd.Timestamp("2024-08-12"))["revival"]["probability"]
    assert abs(p - EXPECTED_REVIVAL_2024_08_12) < 1e-3


def test_demo_pivot_rows_reproduce(service):
    """Narrative from reports/MVP_DEMO_SCENARIO.md must hold end to end."""
    rows = {}
    for date_str, _ in PIVOT_DATES:
        ts = pd.Timestamp(date_str)
        pred = service.predict(DEMO_CELL, ts)
        bundle = build_cards_with_bands(service, DEMO_CELL, ts, pred)
        rows[date_str] = {t: pred[t]["probability"] for t in ("onset", "break", "revival", "dry_spell")}
    # false onset day: very low onset AND break probability (break forms 2 days later)
    assert rows["2024-06-07"]["onset"] < 0.05
    assert rows["2024-06-07"]["break"] < 0.1
    # dry spell eve / trace rain: persistence cards sticky
    assert rows["2024-08-08"]["dry_spell"] > 0.9
    assert rows["2024-08-11"]["break"] > 0.9
    # revival day: ML card fires while persistence cards still lag
    assert rows["2024-08-12"]["revival"] > 0.6
    assert abs(rows["2024-08-12"]["revival"] - EXPECTED_REVIVAL_2024_08_12) < 1e-3


def test_demo_run_succeeds(service):
    from src.serving.demo import run
    out = run()
    assert len(out["rows"]) == len(PIVOT_DATES)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))