"""End-to-end persistence demonstration (Phase I-B).

Run:  python -m src.database.persist --cell 10.75_77.5 --date 2024-08-12

Computes a forecast through the same frozen serving pipeline as the API
(ModelService.predict + rules.build_cards_with_bands) and persists one
`forecasts` row + 5 `advisories` rows. Does not modify serving/core code;
`src.serving` remains the single source of the prediction.
"""
from __future__ import annotations

import argparse
import json

import pandas as pd

from src.database import config
from src.database.db import connect
from src.database.repository import FROZEN_VERSION, store_forecast_bundle
from src.serving.models import default_service, freeze_digest
from src.serving.registry import CellRegistry
from src.serving.rules import build_cards_with_bands
from src.serving.store import default_store


def build_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cell", required=True, help="grid cell id, e.g. 10.75_77.5")
    p.add_argument("--date", required=True, help="ISO date, e.g. 2024-08-12")
    p.add_argument("--json", action="store_true", help="print the persisted bundle as JSON")
    return p.parse_args()


def main() -> None:
    if not config.database_url():
        raise SystemExit(
            "DATABASE_URL not set. Copy .env.example to .env and fill in the DSN first.")
    args = build_args()
    cell_id = args.cell
    date = pd.Timestamp(args.date)
    if not CellRegistry.is_valid_id(cell_id):
        raise SystemExit(f"invalid cell id: {cell_id!r}")

    store = default_store()
    service = default_service(store)
    digest = freeze_digest()

    pred = service.predict(cell_id, date)
    bundle = build_cards_with_bands(service, cell_id, date, pred)
    probabilities = {t: pred[t]["probability"]
                     for t in ("onset", "break", "revival", "dry_spell")}

    with connect() as session:
        fid = store_forecast_bundle(
            session,
            cell_id=cell_id,
            forecast_date=date,
            probabilities=probabilities,
            model_version=FROZEN_VERSION,
            mode="historical/demo",
            bundle=bundle,
        )

    out = {
        "forecast_id": fid,
        "cell_id": cell_id,
        "forecast_date": date.date().isoformat(),
        "probabilities": {k: round(float(v), 4) for k, v in probabilities.items()},
        "dominant_state": bundle["dominant"],
        "model_version": FROZEN_VERSION,
        "freeze_digest": digest,
        "persisted": True,
    }
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Persisted forecast {fid} for {cell_id} @ {date.date().isoformat()} "
              f"[dominant={bundle['dominant']}, version={FROZEN_VERSION}, digest={digest}]")


if __name__ == "__main__":
    main()