"""Reproducible MVP demo (contract: reports/MVP_DEMO_SCENARIO.md).

Loads the REAL frozen pipeline (CellRegistry + ObservationStore + ModelService) and
produces the exact pivot rows for the demo scenario. No hardcoded predictions: every
number comes from the frozen models on demand. Run:  python -m src.serving.demo
"""
from __future__ import annotations

import pandas as pd

from src.serving.models import ModelService
from src.serving.registry import CellRegistry
from src.serving.rules import build_cards_with_bands, band_of, band_meaning
from src.serving.store import ObservationStore

DEMO_CELL = "10.75_77.5"
PIVOT_DATES = [
    ("2024-06-07", "False onset day (40.1 mm rain; calibrated low onset P)"),
    ("2024-08-08", "Dry-spell eve (sticky persistence cards active)"),
    ("2024-08-11", "Trace rain (revival still quiet)"),
    ("2024-08-12", "REVIVAL DAY - ML card is the signal"),
    ("2024-09-29", "Late-season second revival (very high P)"),
]
EXPECTED_REVIVAL_2024_08_12 = 0.6047


def run() -> dict:
    store = ObservationStore.from_file()
    registry = CellRegistry.from_matrix(store.matrix)
    service = ModelService(store, matrix=store.matrix)

    cell = registry.get(DEMO_CELL)
    print("=" * 78)
    print("MVP DEMO  -  SIH26086 Monsoon Decision Support")
    print(f"Cell {DEMO_CELL}  lat={cell['lat']} lon={cell['lon']} region={cell['region']}")
    print(f"Spatial unit: {cell['admin_note']} (0.25 deg pilot grid cell)")
    print(f"Data mode: {service.provenance()['data_mode']}")
    print("=" * 78)

    rows = []
    for date_str, note in PIVOT_DATES:
        ts = pd.Timestamp(date_str)
        pred = service.predict(DEMO_CELL, ts)
        probs = {t: pred[t]["probability"] for t in ("onset", "break", "revival", "dry_spell")}
        bundle = build_cards_with_bands(service, DEMO_CELL, ts, pred)
        row = service.store.row(DEMO_CELL, ts)
        sig = bundle["current_signal"]
        rows.append({
            "date": date_str,
            "note": note,
            "obs_mm": sig["rain_t_mm"],
            "onset": probs["onset"], "break": probs["break"],
            "revival": probs["revival"], "dry_spell": probs["dry_spell"],
            "dominant": bundle["dominant"],
            "signal": f"{sig['rainfall_trend']}/{sig['rainfall_regime']}",
        })
        print(f"\n--- {date_str}  ({note})")
        print(f"    obs rain_t={sig['rain_t_mm']}mm  signal={sig['rainfall_trend']}/{sig['rainfall_regime']}")
        for c in bundle["cards"]:
            print(f"    {c['state_label']:<10s} {c['probability_pct']:>6.1f}%  {c['band']:<10s} {c['band_meaning']}")
        print(f"    >>> dominant: {bundle['dominant']}")

    rev = probs_for(service, DEMO_CELL, "2024-08-12", "revival")
    assert abs(rev - EXPECTED_REVIVAL_2024_08_12) < 1e-3, \
        f"revival {rev} != frozen {EXPECTED_REVIVAL_2024_08_12}"
    print("\n" + "=" * 78)
    print(f"CHECK: revival probability on 2024-08-12 == {EXPECTED_REVIVAL_2024_08_12}  (PASS)")
    print(f"Explanation top feature: th_accel (see /explain sensitivity table)")
    print("Freeze:", service.provenance()["freeze_file"], "digest", service.freeze_digest)
    return {"rows": rows}


def probs_for(service: ModelService, cell: str, date: str, target: str) -> float:
    return float(service.predict(cell, pd.Timestamp(date))[target]["probability"])


if __name__ == "__main__":
    run()