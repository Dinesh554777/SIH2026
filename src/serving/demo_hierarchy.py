"""Demo/simulated administrative hierarchy for the officer-dashboard drill-down.

Honest-to-gates: authoritative GIS boundaries are NOT available (see geography
routing gate), so this module serves a clearly-labelled DEMO hierarchy that maps
each demo village to a REAL pilot grid cell (0.25 deg). Every number shown for a
village is the frozen model output of its mapped cell - village-level predictions
are an approximation, never a fabricated village-specific model.
"""
from __future__ import annotations

MODE = "demo/simulated"
NOTE = (
    "Demo hierarchy for the SIH 2026 prototype. Administrative names are "
    "representative examples, NOT authoritative GIS boundaries. Village numbers "
    "are approximated from the mapped pilot grid cell (0.25 deg, ~25 x 25 km)."
)

DEMO_HIERARCHY = [
    {
        "state": {"geography_id": "TN", "name": "Tamil Nadu"},
        "districts": [
            {
                "district": {"geography_id": "TN-thanjavur", "name": "Thanjavur"},
                "blocks": [
                    {
                        "block": {"geography_id": "TN-orathanadu", "name": "Orathanadu"},
                        "villages": [
                            {"village_id": "TN-ORA-001",
                             "name": "Demo Agricultural Village", "cell_id": "10.75_77.5"},
                            {"village_id": "TN-ORA-002",
                             "name": "Demo Irrigated Village", "cell_id": "10.75_77.25"},
                            {"village_id": "TN-ORA-003",
                             "name": "Demo Rainfed Village", "cell_id": "10.0_76.25"},
                        ],
                    }
                ],
            }
        ],
    },
]


def resolve_village(village_id: str) -> dict | None:
    """Return {village:..., block:..., district:..., state:..., cell_id} or None."""
    for st in DEMO_HIERARCHY:
        for dist in st["districts"]:
            for blk in dist["blocks"]:
                for v in blk["villages"]:
                    if v["village_id"] == village_id:
                        return {
                            "state": st["state"],
                            "district": dist["district"],
                            "block": blk["block"],
                            "village": v,
                            "cell_id": v["cell_id"],
                        }
    return None


def filter_to_registry(valid_cell_ids: set[str]) -> dict:
    """Keep only villages whose mapped cell exists in the pilot registry."""
    tree = []
    for st in DEMO_HIERARCHY:
        districts = []
        for dist in st["districts"]:
            blocks = []
            for blk in dist["blocks"]:
                villages = [v for v in blk["villages"] if v["cell_id"] in valid_cell_ids]
                if villages:
                    blocks.append({
                        "block": blk["block"],
                        "villages": villages,
                        "pilot_cell": villages[0]["cell_id"],
                    })
            if blocks:
                districts.append({"district": dist["district"], "blocks": blocks,
                                  "pilot_cell": blocks[0]["pilot_cell"]})
        if districts:
            tree.append({"state": st["state"], "districts": districts,
                         "pilot_cell": districts[0]["pilot_cell"]})
    return {"mode": MODE, "note": NOTE, "hierarchy": tree,
            "pilot_cell_count": len(valid_cell_ids)}