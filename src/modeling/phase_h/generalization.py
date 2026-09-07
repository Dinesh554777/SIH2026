"""Phase H7: generalization analysis for promising candidates on VALIDATION (2022-2023).

Covers yearly (2022/2023), regional (TN/MH/KA), and cell-level spread for the frozen
reference vs the best Phase H candidate per target. PR-AUC/recall/precision/calibration
reported for rare targets (onset, revival) per H7.1.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.modeling import evaluate as ev  # noqa: E402
from src.modeling.common import (PREDICTIONS_DIR, PROJECT_ROOT, PUBLIC_TARGETS,  # noqa: E402
                                 region_of)
from src.modeling.metrics import compute_metrics  # noqa: E402
from src.modeling.phase_h import ablation_val as AV  # noqa: E402
from src.modeling.phase_h import modeling as M  # noqa: E402

# Promising candidates from H6 (per target): (group, model) to deep-dive
CANDIDATES = {
    "onset": None,       # frozen persistence wins
    "break": None,       # frozen persistence wins
    "revival": ("B", "xgboost"),
    "dry_spell": None,   # frozen persistence wins
}


def _aux(preds: pd.DataFrame, region_map) -> pd.DataFrame:
    out = preds.copy()
    out["year"] = pd.to_datetime(out["date"]).dt.year.astype(int)
    out["region"] = out["cell_id"].map(region_map)
    return out


def yearly(rec: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rec)


def main() -> None:
    df = pd.read_parquet(PROJECT_ROOT / "data" / "processed" / "phase_h_matrix.parquet")
    region_map = df.groupby("cell_id")["bbox_guess"].first().map(region_of).to_dict()
    preds = M.load_group_predictions()
    preds = _aux(preds, region_map)
    ref = AV.load_frozen_reference_val(df)
    ref = _aux(ref, region_map)

    out = {"candidates": CANDIDATES}
    for tgt in PUBLIC_TARGETS:
        cand = CANDIDATES[tgt]
        if cand is None:
            out[tgt] = {"decision": "keep frozen persistence", "reason": "no candidate beat frozen reference on validation"}
            continue
        g, model = cand
        d_cand = preds[(preds["target"] == tgt) & (preds["group"] == g) &
                       (preds["model"] == model) & (preds["split"] == "val")]
        d_ref = ref[(ref["target"] == tgt)]  # frozen reference for this target (val only)

        per_year = {}
        for yr in (2022, 2023):
            per_year[str(yr)] = {
                "cand": compute_metrics(d_cand[d_cand["year"] == yr]["observed_label"].to_numpy(),
                                        d_cand[d_cand["year"] == yr]["probability"].to_numpy()),
                "frozen": compute_metrics(d_ref[d_ref["year"] == yr]["observed_label"].to_numpy(),
                                          d_ref[d_ref["year"] == yr]["probability"].to_numpy()),
            }
        # region (2022 + 2023 pooled)
        per_region = {}
        for r in ("TN", "MH", "KA"):
            dc = d_cand[d_cand["region"] == r]; dr = d_ref[d_ref["region"] == r]
            if dc.empty or dr.empty:
                continue
            per_region[r] = {
                "cand": compute_metrics(dc["observed_label"].to_numpy(), dc["probability"].to_numpy()),
                "frozen": compute_metrics(dr["observed_label"].to_numpy(), dr["probability"].to_numpy()),
            }
        recs = {}
        for k in ("yearly", "regional"):
            rows = []
            if k == "yearly":
                for yr in (2022, 2023):
                    rows.append({"group_by": "year", "key": str(yr),
                                 "cand_brier": per_year[str(yr)]["cand"]["brier"],
                                 "frozen_brier": per_year[str(yr)]["frozen"]["brier"],
                                 "cand_pr_auc": per_year[str(yr)]["cand"]["pr_auc"],
                                 "cand_ece": per_year[str(yr)]["cand"]["ece"],
                                 "cand_recall": per_year[str(yr)]["cand"]["recall"],
                                 "cand_precision": per_year[str(yr)]["cand"]["precision"],
                                 "cand_n_pos": per_year[str(yr)]["cand"]["n_pos"]})
            else:
                for r in per_region:
                    rows.append({"group_by": "region", "key": r,
                                 "cand_brier": per_region[r]["cand"]["brier"],
                                 "frozen_brier": per_region[r]["frozen"]["brier"],
                                 "cand_pr_auc": per_region[r]["cand"]["pr_auc"],
                                 "cand_ece": per_region[r]["cand"]["ece"],
                                 "cand_recall": per_region[r]["cand"]["recall"],
                                 "cand_precision": per_region[r]["cand"]["precision"],
                                 "cand_n_pos": per_region[r]["cand"]["n_pos"]})
            recs[k] = pd.DataFrame(rows)
        out[tgt] = {
            "decision": "candidate",
            "group": g, "model": model,
            "overall": compute_metrics(d_cand["observed_label"].to_numpy(),
                                       d_cand["probability"].to_numpy()).get("brier"),
            "frozen_overall_brier": compute_metrics(d_ref["observed_label"].to_numpy(),
                                                    d_ref["probability"].to_numpy()).get("brier"),
            "yearly": recs["yearly"].to_dict("records"),
            "regional": recs["regional"].to_dict("records"),
        }
        print(f"\n===== {tgt} candidate {g}/{model} =====")
        print(recs["yearly"].to_string(index=False))
        print(recs["regional"].to_string(index=False))

    import json
    from src.modeling.common import write_json
    write_json(out, PREDICTIONS_DIR / "phase_h" / "generalization_val.json")
    print("\nwrote generalization_val.json")


if __name__ == "__main__":
    main()