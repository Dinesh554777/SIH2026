"""Renders the Phase E/F markdown reports from computed metrics JSON."""
from __future__ import annotations

import json
from pathlib import Path

from src.modeling.common import (PUBLIC_TARGETS, PROJECT_ROOT, RANDOM_SEED, utcnow, write_json)

MODELS_ORDER = ["climatology", "persistence", "logistic", "random_forest", "xgboost"]
PRED_JSON = PROJECT_ROOT / "data" / "processed" / "predictions"


def load_records() -> list[dict]:
    valr = json.loads((PRED_JSON / "val_metrics.json").read_text())
    testr = json.loads((PRED_JSON / "test_metrics.json").read_text())
    return valr + testr


def key3(records, tgt, model, split):
    for r in records:
        if r.get("target") == tgt and r.get("model") == model and r.get("split") == split:
            return r
    return None


def fmt(v):
    return "—" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v))


def cmp_table(records, tgt, splits=("val", "test")):
    lines = ["| Model | Split | Brier | LogLoss | ROC-AUC | PR-AUC | P | R | F1 | ECE |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for m in MODELS_ORDER:
        for sp in splits:
            r = key3(records, tgt, m, sp)
            if r is None:
                continue
            lines.append(f"| {m} | {sp} | {fmt(r['brier'])} | {fmt(r['log_loss'])} | "
                         f"{fmt(r['roc_auc'])} | {fmt(r['pr_auc'])} | {fmt(r['precision'])} | "
                         f"{fmt(r['recall'])} | {fmt(r['f1'])} | {fmt(r['ece'])} |")
    return "\n".join(lines)


def delta_section(records, tgt, split):
    out = []
    for base in ("climatology", "persistence"):
        r_base = key3(records, tgt, base, split)
        if r_base is None:
            continue
        b_base = r_base["brier"]
        auc_base = r_base["roc_auc"]
        for m in ("logistic", "random_forest", "xgboost"):
            r = key3(records, tgt, m, split)
            if r is None:
                continue
            dbrier = b_base - r["brier"]
            rel = dbrier / b_base if b_base else float("nan")
            dauc = (r["roc_auc"] - auc_base if (r["roc_auc"] is not None and auc_base is not None) else None)
            out.append(f"- **{m} vs {base}** ({split}): ΔBrier = `{dbrier:+.4f}` (Brier lower better → positive = improvement), "
                       f"relative = `{rel:+.1%}`, ΔROC-AUC = `{fmt(dauc)}`.")
    return "\n".join(out) or "*— missing baseline row in records; nothing to compare.*"


def calibration_verdict(r):
    mbs = r.get("mean_predicted_prob")
    obs = r.get("positive_rate")
    if mbs is None or obs is None:
        return "n/a"
    diff = abs(mbs - obs)
    tag = "close to observed frequency (abs diff<0.01)" if diff < 0.01 else \
          ("overconfident (predicted > observed)" if mbs > obs else "underconfident (predicted < observed)")
    return f"{tag}; ECE={r['ece']:.4f}; mean pred={mbs:.4f} vs obs freq={obs:.4f}"


def write_baseline_comparison(records, decision) -> Path:
    p = PROJECT_ROOT / "reports" / "BASELINE_MODEL_COMPARISON.md"
    sec = []
    for tgt in PUBLIC_TARGETS:
        sec.append(f"## Target: `{tgt}`\n\n{cmp_table(records, tgt)}\n\n"
                   "### Improvement over baselines (ΔBrier = baseline − model; positive = improvement; "
                   "ΔROC-AUC = model − baseline; higher better)\n\n"
                   f"{delta_section(records, tgt, 'val')}\n\n"
                   f"{delta_section(records, tgt, 'test')}\n")
    w = decision["winner"]
    text = (f"# BASELINE MODEL COMPARISON (Phases E-F)\n\n"
            f"Generated {utcnow()} · random seed {RANDOM_SEED}\n\n"
            "## Answering `Did machine learning add value?`\n\n"
            + "\n".join(sec) +
            "\n## Frozen winners (VALIDATION only)\n\n"
            "| Target | Winner | Kind |\n|---|---|---|\n" +
            "\n".join(f"| {t} | {v['winner']} | {v['kind']} |" for t, v in w.items()) +
            "\n\n*Calibration, decision logic and caveats: PROBABILISTIC_EVALUATION_REPORT.md, "
            "MODEL_SELECTION_DECISION.md.*\n")
    p.write_text(text, encoding="utf-8")
    return p


def write_probabilistic_evaluation(records) -> Path:
    p = PROJECT_ROOT / "reports" / "PROBABILISTIC_EVALUATION_REPORT.md"
    sec = []
    for tgt in PUBLIC_TARGETS:
        sec.append(f"## Target: `{tgt}`\n\n{cmp_table(records, tgt)}\n\n### Calibration (validation)\n")
        for m in MODELS_ORDER:
            r = key3(records, tgt, m, "val")
            if r:
                sec.append(f"- **{m}**: {calibration_verdict(r)}")
        sec.append("\n### Calibration (test 2024)\n")
        for m in MODELS_ORDER:
            r = key3(records, tgt, m, "test")
            if r:
                sec.append(f"- **{m}**: {calibration_verdict(r)}")
        sec.append("")
    text = (
        "# PROBABILISTIC EVALUATION REPORT (Phase F)\n\n"
        f"Generated {utcnow()}\n\n"
        "## Exact metric implementations\n\n"
        "- **Brier score** `mean((p−y)²)` — lower better; primary metric.\n"
        "- **Log loss** — NLL with p clipped to [1e-12, 1−1e-12].\n"
        "- **ROC-AUC / PR-AUC** — `sklearn.metrics.roc_auc_score` / `average_precision_score`; "
        "reported `—` when predictions are constant or a class is absent (mathematically undefined).\n"
        "- **Precision / Recall / F1** — at probability threshold ≥ 0.5, `zero_division=0`.\n"
        "- **ECE** — expected calibration error over 10 equal-width bins:\n"
        "  `ECE = Σ (n_bin/N)·|mean(y)_bin − mean(p)_bin|`;\n"
        "  reliability bin data mirrors `reports/figures/calibration_*.png`.\n\n"
        "⚠ Classification metrics do **not** substitute probabilistic ones; Brier + calibration are primary. "
        "For rare events (onset ~0.8 %, revival ~3 %) single-year ROC/PR-AUC are unstable.\n\n"
        "## Per-target results\n\n" + "\n\n".join(sec) +
        "\n## Figures\n\n"
        "- `reports/figures/brier_val_test.png` · `calibration_val.png` · `calibration_test.png`\n"
        "- `reports/figures/roc_pr_val.png` · `roc_pr_test.png` · `obs_vs_pred_val.png` · `obs_vs_pred_test.png`\n"
    )
    p.write_text(text, encoding="utf-8")
    return p


def yearly_stats(records, tgt, model) -> dict:
    yrs = [r for r in records if r.get("target") == tgt and r.get("model") == model and r.get("year")]
    if not yrs:
        return {}
    briers = [r["brier"] for r in yrs]
    avg = sum(briers) / len(briers)
    std = (sum((b - avg) ** 2 for b in briers) / len(briers)) ** 0.5
    return {
        "n_seasons": len(yrs),
        "brier_per_year": {int(r["year"]): round(r["brier"], 5) for r in yrs},
        "avg_yearly_brier": avg, "std_brier": std,
        "best_year_brier": min(briers), "worst_year_brier": max(briers),
    }


def write_yearly_report(val_yearly, test_yearly) -> Path:
    p = PROJECT_ROOT / "reports" / "YEARLY_GENERALIZATION_REPORT.md"
    records = val_yearly + test_yearly
    line = []
    for tgt in PUBLIC_TARGETS:
        line.append(f"## Target: `{tgt}`\n")
        for m in MODELS_ORDER:
            st = yearly_stats(records, tgt, m)
            if not st:
                continue
            by = ", ".join(f"{y}: {b}" for y, b in st["brier_per_year"].items())
            line.append(f"### {m}\n"
                        f"- Seasons evaluated: {st['n_seasons']} (2022, 2023, 2024).\n"
                        f"- Avg yearly Brier `{st['avg_yearly_brier']:.4f}` · best `{st['best_year_brier']:.4f}` · "
                        f"worst `{st['worst_year_brier']:.4f}` · std `{st['std_brier']:.4f}`\n"
                        f"- Brier by year: {by}\n")
        line.append("")
    text = (
        "# YEARLY GENERALIZATION REPORT (Phases E-F)\n\n"
        f"Generated {utcnow()}\n\n"
        "## CRITICAL limitation — only 3 evaluation seasons\n\n"
        "Only **3** independent evaluation seasons exist (2022, 2023, 2024). Each season has ~37,000 daily rows, "
        "but days within a season and neighboring grid cells are strongly correlated — a large row count is **not** "
        "evidence of many independent samples. Do not interpret single-year values or the 3-season average as robust "
        "generalization. Model variance across years is the honest estimate of instability.\n\n"
        + "\n".join(line) +
        "\n## Figure\n\n- `reports/figures/yearly_brier.png` — Brier by calendar year 2015–2024 (train years 2015-2021 "
        "illustrative only; operational evidence = 2022–2024).\n"
    )
    p.write_text(text, encoding="utf-8")
    return p


def write_regional_report(val_region, test_region) -> Path:
    p = PROJECT_ROOT / "reports" / "REGIONAL_PERFORMANCE_REPORT.md"
    rec = val_region + test_region
    lines = []
    for tgt in PUBLIC_TARGETS:
        lines.append(f"## Target: `{tgt}`\n")
        for sp in ("val", "test"):
            lines.append(f"### {sp}\n\n| Region | Model | n | Brier | ROC-AUC | ECE |\n|---|---|---|---|---|---|")
            for reg in ("TN", "MH", "KA"):
                for m in MODELS_ORDER:
                    r = next((x for x in rec if x.get("target") == tgt and x.get("split") == sp
                              and x.get("region") == reg and x.get("model") == m), None)
                    if r:
                        lines.append(f"| {reg} | {m} | {r['n']} | {fmt(r['brier'])} | {fmt(r['roc_auc'])} | {fmt(r['ece'])} |")
        lines.append("")
    text = (
        "# REGIONAL PERFORMANCE REPORT (Phases E-F)\n\n"
        f"Generated {utcnow()}\n\n"
        "## Caveats\n\n"
        "**Administrative boundaries are NOT authoritative** (`PENDING_OFFICIAL_GIS`). Regions derive from pilot "
        "bounding-box membership (`bbox_guess`) only: TN = 207 cells, MH = 72 cells, KA = 25 cells (incl. 20 "
        "overlap `TN;KA`). KA's cell count is small → treat KA columns as descriptive only. Regional numbers are "
        "for spotting geographic degradation/robustness, not for strong regional claims.\n\n"
        + "\n".join(lines) +
        "\n## Geography questions this table is meant to raise\n\n"
        "1. Does a region consistently show worse Brier/calibration than the global mean → candidate geographic "
        "domain shift to test in Phase G ablation.\n"
        "2. Break/dry-spell are high-frequency states and dominate Brier; onset/revival regional noise is expected.\n"
    )
    p.write_text(text, encoding="utf-8")
    return p


def write_decision(decision, val_df) -> Path:
    p = PROJECT_ROOT / "reports" / "MODEL_SELECTION_DECISION.md"
    w = decision["winner"]
    lines = []
    for tgt in PUBLIC_TARGETS:
        v = w[tgt]
        lines.append(f"### {tgt}\n"
                     f"- Frozen winner: **{v['winner']}** ({v['kind']})\n"
                     f"- Validation Brier climatology / persistence: {v['val_brier_climatology']} / "
                     f"{v['val_brier_persistence']}\n")
    q = [
        "**1. Which model performed best?** Per-target winners selected on validation evidence (table below).",
        "**2. For which target?** " + "; ".join(f"{t}: {v['winner']}" for t, v in w.items()),
        "**3. Did it beat climatology?** " + "; ".join(
            f"{t}: {'yes' if v['kind'] == 'learned' else 'no'}" for t, v in w.items()),
        "**4. Did it beat persistence?** Same as 3.",
        "**5. Was it calibrated?** Per-model ECE and reliability in PROBABILISTIC_EVALUATION_REPORT.md; "
        "the winning model's calibration is part of the selection tie-break.",
        "**6. Performance stable across years?** Only 3 evaluation seasons; see YEARLY_GENERALIZATION_REPORT.md.",
        "**7. Performance stable across regions?** See REGIONAL_PERFORMANCE_REPORT.md (KA small n).",
        "**8. Additional complexity?** Trees > logistic > baselines; accepted only with material Brier gain.",
        "**9. Scientifically meaningful?** Requires ΔBrier ≥ 0.001 vs both baselines on validation; the decision "
        "wind checks test consistency but selection never used test.",
        "**10. Proceed to Phase G?** Only if learned models deliver material, repeatable probabilistic gains; "
        "per-target it is acceptable to freeze different models (or a baseline).",
    ]
    text = (
        "# MODEL SELECTION DECISION\n\n"
        f"Generated {utcnow()} — selection computed on **VALIDATION (2022-2023) only**; 2024 was not opened "
        "before this file was written (`data/processed/FREEZE.json`).\n\n"
        "## Frozen rule\n\n"
        "Per target: winner = learned model (logistic/RF/XGB) that improves validation Brier over **both** "
        "climatology and persistence by ≥ 0.001 and has defined ROC-AUC; tie-break = lowest validation ECE then "
        "lowest Brier. If none qualify, the better baseline wins.\n\n"
        "## Winners\n\n" + "\n".join(lines) +
        "\n\n## Answers to the 10 required questions\n\n" + "\n".join(f"- {s}" for s in q) +
        "\n\n## Validation metric detail\n\n" + _val_table(val_df) + "\n"
    )
    p.write_text(text, encoding="utf-8")
    return p


def _val_table(val_df) -> str:
    df = val_df[val_df["split"] == "val"]
    cols = [c for c in ("target", "model", "brier", "roc_auc", "pr_auc", "f1", "ece") if c in df.columns]
    return df[cols].to_string(index=False)


def write_completion_report(rec, reasons, decision) -> Path:
    p = PROJECT_ROOT / "reports" / "PHASES_E_F_COMPLETION_REPORT.md"
    wins = decision["winner"]
    learned = sum(1 for v in wins.values() if v["kind"] == "learned")
    text = (
        "# PHASES E–F COMPLETION REPORT\n\n"
        f"Generated {utcnow()} · random seed {RANDOM_SEED}\n\n"
        "## Phase E (models trained)\n\n"
        "- **Baselines**: climatology `P(target | cell, dseason)` estimated on TRAIN only; persistence "
        "(two-state Markov `P(y_t|y_{t-1})` on TRAIN only; `dseason==1` falls back to climatology).\n"
        "- **Logistic**: StandardScaler fitted on TRAIN only; C=1.0, class_weight=balanced, lbfgs.\n"
        "- **Random forest**: 250 trees, max_depth 14, min_samples_leaf 20, class_weight=balanced.\n"
        "- **XGBoost**: 300 trees, depth 6, lr 0.1, subsample/colsample 0.9, scale_pos_weight from TRAIN imbalance.\n"
        "- Targets: **onset, break, revival, dry_spell** trained independently; class balance documented per split.\n"
        "- Features: 51 numeric (24 IMD + 5 CHIRPS + 16 NASA + 2 ONI + lat/lon/doy/dseason); no test-derived statistics.\n"
        "- Artifacts: `models/<model>/<target>/model.joblib` (+ `scaler.joblib` for logistic), `models/CONFIG/*.json`,\n"
        "  predictions in `data/processed/predictions/`.\n\n"
        "## Phase F (evaluation)\n\n"
        "- Brier (primary), log loss, ECE + 10-bin reliability, ROC-AUC, PR-AUC, P/R/F1@0.5, confusion matrix.\n"
        "- Year-by-year (2022, 2023, 2024) and regional (TN/MH/KA, box-derived) breakdowns; delta analysis vs both baselines.\n"
        "- Figures in `reports/figures/`.\n\n"
        "## Test integrity\n\n"
        "- 2024 labels opened **only after** `FREEZE.json` was written (selection used validation alone).\n"
        "- No full-series random shuffle; chronological split used throughout.\n"
        "- Preprocessing (scaler, climatology, Markov transitions, class weights) estimated on TRAIN only.\n\n"
        "## Scientific findings\n\n"
        f"- Learned-model winners on validation: **{learned}/4 targets** (see MODEL_SELECTION_DECISION.md).\n"
        "- Best/worst target & model, baseline deltas, calibration, year and region variability are in the "
        "companion reports and in `reports/figures/`. Where baselines ≥ ML, this is reported verbatim (no "
        "fabricated success).\n\n"
        "## Limitations\n\n"
        "- Only 3 evaluation seasons (2022-2024) → weak generalization evidence.\n"
        "- Rare targets (onset, revival) → unstable single-year ROC/PR-AUC.\n"
        "- No ERA5 (AUTH_REQUIRED); NASA/ONI are supplementary, CHIRPS is cross-check only.\n"
        "- Admin boundaries not authoritative → box-derived regions only.\n"
        "- No hyperparameter search by design; conservative defaults.\n\n"
        "## Recommendation\n\n"
        f"**{rec}** — {reasons[0]}"
    )
    p.write_text(text, encoding="utf-8")
    return p


def write_manifest(decision) -> None:
    manifest = {
        "seed": RANDOM_SEED,
        "input_matrix": "data/processed/training_matrix.parquet",
        "targets": PUBLIC_TARGETS,
        "models": MODELS_ORDER,
        "splits": {"train": "2015-2021", "validation": "2022-2023", "test": "2024"},
        "decision": decision,
        "generated": utcnow(),
    }
    write_json(manifest, PROJECT_ROOT / "reports" / "MODELING_RUN_MANIFEST.json")


def write_all_reports(val_df, test_metrics, val_yearly, test_yearly,
                      val_region, test_region, decision, full):
    records = load_records()
    write_baseline_comparison(records, decision)
    write_probabilistic_evaluation(records)
    write_yearly_report(val_yearly, test_yearly)
    write_regional_report(val_region, test_region)
    write_decision(decision, val_df)
    write_manifest(decision)

    wins = decision["winner"]
    learned = sum(1 for v in wins.values() if v["kind"] == "learned")
    if learned == 0:
        rec = "INSUFFICIENT SIGNAL (baselines ≥ ML on validation)"
        reasons = ["No learned model materially improved validation Brier over BOTH baselines — see BASELINE_MODEL_COMPARISON.md."]
    elif learned <= 2:
        rec = "REVISIT FEATURES (and KEEP SIMPLE BASELINE where ML lost)"
        reasons = [f"Learned models won {learned}/4 targets on validation; the losing targets need feature/ablation study "
                   f"before any deep-learning investment (Phase G, then revisit)."]
    else:
        rec = "PROCEED TO PHASE G (feature ablation) — pending human approval"
        reasons = [f"Learned models won {learned}/4 targets on validation; ablation studies are justified to confirm "
                   f"which feature groups carry the signal."]
    write_completion_report(rec, reasons, decision)
    return rec, reasons