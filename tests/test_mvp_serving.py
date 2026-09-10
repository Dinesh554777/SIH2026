"""MVP serving tests: frozen inference integrity, determinism, decision rules.

Run:  python -m pytest tests/test_mvp_serving.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.serving import config as C  # noqa: E402
from src.serving.models import ModelService  # noqa: E402
from src.serving.persistence_params import compute_params, export_params  # noqa: E402
from src.serving.registry import CellRegistry  # noqa: E402
from src.serving.rules import (BANDS, band_of, build_cards_with_bands,  # noqa: E402
                               apply_rules, dominant_state)
from src.serving.store import ObservationStore  # noqa: E402

DEMO_CELL = "10.75_77.5"
REVIVAL_2024_08_12 = 0.6047


@pytest.fixture(scope="module")
def store():
    return ObservationStore.from_file()


@pytest.fixture(scope="module")
def service(store):
    return ModelService(store, matrix=store.matrix)


@pytest.fixture(scope="module")
def registry(store):
    return CellRegistry.from_matrix(store.matrix)


def test_deterministic_predictions(service):
    p1 = service.predict(DEMO_CELL, pd.Timestamp("2024-08-12"))
    p2 = service.predict(DEMO_CELL, pd.Timestamp("2024-08-12"))
    for t in C.TARGETS:
        assert p1[t]["probability"] == p2[t]["probability"]
        assert 0.0 <= p1[t]["probability"] <= 1.0


def test_target_mapping(service):
    pred = service.predict(DEMO_CELL, pd.Timestamp("2024-08-12"))
    assert set(C.TARGETS) == set(pred.keys()) - {"cell_id", "forecast_date"}
    for t in C.TARGETS:
        assert "probability" in pred[t]
        assert "model" in pred[t]


def test_frozen_model_spec(service):
    # revival must be XGBoost + Group B; others persistence (FREEZE_H)
    pred = service.predict(DEMO_CELL, pd.Timestamp("2024-08-12"))
    assert pred["revival"]["model"] == "xgboost"
    assert pred["revival"]["feature_group"] == "B_temporal"
    assert pred["revival"]["n_features"] == 64
    for t in C.PERSISTENCE_TARGETS:
        assert pred[t]["model"] == "persistence"


def test_revival_feature_order_matches_artifact(service):
    cfg = json.load(open(C.REVIVAL_DIR / "CONFIG.json", encoding="utf-8"))
    assert service.revival_features == list(cfg["features"])
    assert len(service.revival_features) == 64
    assert "th_accel" in service.revival_features
    # imputer must be fitted on the SAME column order (64 entries)
    assert len(service.imputer.statistics_) == 64


def test_revival_matches_frozen_2024(service):
    """Serving reproduction == single post-freeze 2024 test pass."""
    rev = service.predict(DEMO_CELL, pd.Timestamp("2024-08-12"))["revival"]["probability"]
    assert abs(rev - REVIVAL_2024_08_12) < 1e-3


def test_persistence_matches_frozen_reference(service):
    """Persistence probabilities must equal the Phase G/H frozen reference table."""
    bp = pd.read_parquet(C.PROCESSED.joinpath("predictions/baseline_predictions.parquet"))
    bp = bp[(bp["model"] == "persistence") & (bp["split"] == "test")]
    test_cells = ["10.75_77.5", "14.5_74.5", "11.5_76.5"]
    for t in C.PERSISTENCE_TARGETS:
        sub = bp[bp["target"] == t]
        for cell in test_cells:
            sub2 = sub[sub["cell_id"] == cell]
            if sub2.empty:
                continue
            date_str = "2024-09-30"
            p = service.predict(cell, pd.Timestamp(date_str))[t]["probability"]
            expected = float(sub2.set_index("date").loc[pd.Timestamp(date_str), "probability"])
            assert abs(p - expected) < 1e-9, f"{t} {cell} differs"


def test_persistence_dseason1_climatology(service):
    # June 1 of a train year uses cell-dseason climatology fallback (dseason==1)
    pred = service.predict(DEMO_CELL, pd.Timestamp("2021-06-01"))
    cell_clim = service._clim_lookup.loc[(DEMO_CELL, 1)]
    for t in C.PERSISTENCE_TARGETS:
        assert np.isclose(pred[t]["probability"], float(cell_clim[f"{t}_clim_p"]), atol=1e-9)


def test_imputation_frozen_median(service):
    cfg = json.load(open(C.REVIVAL_DIR / "CONFIG.json", encoding="utf-8"))
    stats = np.array(cfg["imputation"]["statistics"])
    assert np.allclose(np.array(service.imputer.statistics_), stats)


def test_band_bounds():
    assert band_of(0.0) == "low"
    assert band_of(0.29) == "low"
    assert band_of(0.30) == "moderate"
    assert band_of(0.59) == "moderate"
    assert band_of(0.60) == "high"
    assert band_of(0.79) == "high"
    assert band_of(0.80) == "very_high"
    assert band_of(1.0) == "very_high"


def test_rules_table_complete():
    result = apply_rules({"onset": 0.5, "break": 0.5, "revival": 0.5, "dry_spell": 0.5})
    assert len(result) == 4
    for card in result:
        assert card["band"] in ("low", "moderate", "high", "very_high")
        assert card["interpretation"]
        assert card["suggested_action"]
        assert "expert_validation" in card


def test_advisory_bundle(service):
    ts = pd.Timestamp("2024-08-12")
    pred = service.predict(DEMO_CELL, ts)
    bundle = build_cards_with_bands(service, DEMO_CELL, ts, pred)
    assert bundle["dominant"] in C.TARGETS
    assert len(bundle["cards"]) == 4
    assert "Disclaimer" in bundle["disclaimer"] or "Disclaimer" in bundle["disclaimer"] or bundle["disclaimer"]
    assert bundle["current_signal"]["rain_t_mm"] is not None
    assert bundle["evidence"]


def test_dominant_state_uses_max():
    p = {"onset": 0.01, "break": 0.91, "revival": 0.60, "dry_spell": 0.92}
    assert dominant_state(p) == "dry_spell"


def test_sensitivity_is_model_grounded(service):
    sens = service.sensitivity(DEMO_CELL, pd.Timestamp("2024-08-12"))
    assert len(sens) >= 5
    names = [s["feature"] for s in sens]
    assert "th_accel" in names
    # delta must be consistent with the frozen model: replacing the actual value with
    # its train median should not change the output when the value already is the median
    ts = pd.Timestamp("2024-06-02")
    row = service.store.row(DEMO_CELL, ts)
    sens2 = service.sensitivity(DEMO_CELL, ts, features=["imd_rain_t"])
    j = service.revival_features.index("imd_rain_t")
    if float(row["imd_rain_t"]) == float(service.imputer.statistics_[j]):
        assert abs(sens2[0]["delta_probability"]) < 1e-9


def test_persistence_params_export_parity(service):
    """G1 gate: exported persistence_params.json must equal on-boot values on restart."""
    path = C.SERVING_DIR / "persistence_params.json"
    export_params(path)
    data = json.loads(path.read_text(encoding="utf-8"))

    for t in ("onset", "break", "revival", "dry_spell"):
        assert abs(data["persistence_transitions"][t]["p11"] - service.trans[t]["p11"]) < 1e-12
        assert abs(data["persistence_transitions"][t]["p01"] - service.trans[t]["p01"]) < 1e-12
    assert abs(data["persistence_transitions"]["revival"]["p01"] - 0.0314) < 1e-4

    cell = DEMO_CELL
    d1 = data["climatology"]["by_cell"][cell]["1"]
    d122 = data["climatology"]["by_cell"][cell]["122"]
    lk = service._clim_lookup
    assert abs(d1["dry_spell_clim_p"] - float(lk.loc[(DEMO_CELL, 1), "dry_spell_clim_p"])) < 1e-12
    assert abs(d122["break_clim_p"] - float(lk.loc[(DEMO_CELL, 122), "break_clim_p"])) < 1e-12


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))