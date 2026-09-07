"""Phase G report rendering: FEATURE_ABLATION_REPORT.md + PHASE_G_COMPLETION_REPORT.md."""
from __future__ import annotations

import pandas as pd

from src.modeling.common import (MODELS_DIR, PROJECT_ROOT, PUBLIC_TARGETS, RANDOM_SEED, utcnow)

ML_MODELS = ["logistic", "random_forest", "xgboost"]
CONFIG_LABEL = {
    "A_imd": "A: IMD only (28)",
    "B_imd_chirps": "B: A + CHIRPS (33)",
    "C_imd_chirps_oni": "C: B + ONI (35)",
    "D_full": "D: full (51, E/F ref)",
}
BASE_LABEL = {"climatology": "climatology", "persistence": "persistence"}


def ny(v):
    return "—" if v is None else (f"{v:.4f}" if isinstance(v, float) else str(v))


def get(records, tgt, config, model):
    return next((r for r in records
                 if r.get("target") == tgt and r.get("config") == config and r.get("model") == model), None)


def config_table(records, tgt, baseline):
    lines = ["| Config | Model | Brier | ROC-AUC | PR-AUC | F1 | ECE |",
             "|---|---|---|---|---|---|---|"]
    for cfg in ["A_imd", "B_imd_chirps", "C_imd_chirps_oni", "D_full"]:
        for m in ML_MODELS:
            r = get(records, tgt, cfg, m)
            if r:
                lines.append(f"| {CONFIG_LABEL[cfg]} | {m} | {ny(r['brier'])} | {ny(r['roc_auc'])} | "
                             f"{ny(r['pr_auc'])} | {ny(r['f1'])} | {ny(r['ece'])} |")
    for base in ("climatology", "persistence"):
        b = baseline.get(f"{tgt}/{base}")
        if b:
            lines.append(f"| {BASE_LABEL[base]} (baseline) | — | {b['brier']:.4f} | {ny(b['roc_auc'])} | "
                         f"{ny(b['pr_auc'])} | — | {ny(b['ece'])} |")
    return "\n".join(lines)


def ablation_story(records, tgt, baseline, split="val"):
    """Per-model ΔBrier between successive configs (+ which is best vs baselines)."""
    out = []
    bclim = baseline[f"{tgt}/climatology"]["brier"]
    bpers = baseline[f"{tgt}/persistence"]["brier"]
    for m in ML_MODELS:
        row = []
        for cfg in ["A_imd", "B_imd_chirps", "C_imd_chirps_oni", "D_full"]:
            r = get(records, tgt, cfg, m)
            row.append((cfg, r["brier"] if r else None))
        pairs = list(zip(row[:-1], row[1:]))
        deltas = " · ".join(f"{a[0]}→{b[0]} Δ={b[1]-a[1]:+.4f}" for a, b in pairs if a[1] is not None and b[1] is not None)
        best = min((x for x in row if x[1] is not None), key=lambda x: x[1])
        beats = f"beats climatology({bclim:.4f})" if best[1] <= bclim - 1e-3 else "does NOT beat climatology"
        beats_p = f"beats persistence({bpers:.4f})" if best[1] <= bpers - 1e-3 else "does NOT beat persistence"
        out.append(f"- **{m}**: best config {best[0]} Brier={best[1]:.4f} ({beats}; {beats_p}) — "
                   f"config deltas: {deltas}")
    return "\n".join(out)


def imp_table(imp, tgt):
    rows = imp.get(tgt, {}).get("xgboost_gain_top15", [])
    if not rows:
        return "*(no importances recorded)*"
    lines = ["| Rank | Feature | XGB gain |", "|---|---|---|"]
    for i, (fname, g) in enumerate(rows, 1):
        lines.append(f"| {i} | `{fname}` | {g:.0f} |")
    return "\n".join(lines)


def write_ablation_report(records, test_records, baseline, decision, imp) -> None:
    p = PROJECT_ROOT / "reports" / "FEATURE_ABLATION_REPORT.md"
    w = decision["winner"]
    sec = []
    for tgt in PUBLIC_TARGETS:
        sec.append(f"## Target: `{tgt}`\n\n### Validation (2022-2023)\n\n{config_table(records, tgt, baseline)}\n\n"
                   "### Does adding feature groups change validation Brier?\n\n"
                   f"{ablation_story(records, tgt, baseline)}\n\n"
                   "### Test 2024 (post-freeze; one evaluation pass)\n\n" + test_table(test_records, tgt) +
                   "\n\n### Feature importance (XGBoost gain, full model)\n\n" + imp_table(imp, tgt) + "\n")
    text = (
        "# FEATURE ABLATION REPORT (Phase G)\n\n"
        f"Generated {utcnow()} · seed {RANDOM_SEED}\n\n"
        "## Design\n\n"
        "Configs share lat/lon/doy/dseason context. All fitted on TRAIN (2015-2021), identical hyperparameters "
        "to Phases E-F, validation = 2022-2023. Config D is the Phase E-F frozen reference (no refit).\n\n"
        "| Config | Feature groups | # features |\n|---|---|---|\n"
        "| A_imd | IMD | 28 |\n| B_imd_chirps | IMD + CHIRPS | 33 |\n"
        "| C_imd_chirps_oni | IMD + CHIRPS + ONI | 35 |\n| D_full | + NASA (full matrix) | 51 |\n\n"
        "**How to read ΔBrier**: negative = worse than previous config; positive = improvement. "
        "Brier lower = better in all cells.\n\n"
        "## Frozen per-target configs (validation only)\n\n"
        "| Target | Config | Model | Kind |\n|---|---|---|---|\n" +
        "\n".join(f"| {t} | {v['config'] or v['model']} | {v['model']} | {v['kind']} |" for t, v in w.items()) +
        "\n\n## Per-target ablation\n\n" + "\n".join(sec) +
        "\n## Figures\n\n- `reports/figures/ablation_brier_val.png` (see completion report).\n"
    )
    p.write_text(text, encoding="utf-8")


def test_table(test_records, tgt):
    lines = ["| Config | Model | Brier | ROC-AUC | PR-AUC | F1 | ECE |", "|---|---|---|---|---|---|---|"]
    for cfg in ["A_imd", "B_imd_chirps", "C_imd_chirps_oni", "D_full"]:
        for m in ML_MODELS:
            r = get(test_records, tgt, cfg, m)
            if r:
                lines.append(f"| {CONFIG_LABEL[cfg]} | {m} | {ny(r['brier'])} | {ny(r['roc_auc'])} | "
                             f"{ny(r['pr_auc'])} | {ny(r['f1'])} | {ny(r['ece'])} |")
    return "\n".join(lines)


def write_completion(df, configs, records, test_records, baseline, decision, imp) -> None:
    p = PROJECT_ROOT / "reports" / "PHASE_G_COMPLETION_REPORT.md"
    w = decision["winner"]
    learned = sum(1 for v in w.values() if v["kind"] == "learned")
    # headline test numbers for frozen learned winners
    fs = []
    for tgt, v in w.items():
        if v["kind"] == "learned":
            r = get(test_records, tgt, v["config"], v["model"])
            fs.append(f"- **{tgt}** frozen {v['config']}/{v['model']}: test Brier {r['brier']:.4f}, "
                      f"ROC {ny(r['roc_auc'])}, ECE {ny(r['ece'])}")
    # per-target headline: does the known E/F pattern persist under ablation?
    summary_lines = []
    for tgt in PUBLIC_TARGETS:
        best_val = None
        for cfg in ["A_imd", "B_imd_chirps", "C_imd_chirps_oni", "D_full"]:
            for m in ML_MODELS:
                r = get(records, tgt, cfg, m)
                if r and (best_val is None or r["brier"] < best_val["brier"]):
                    best_val = r
        if best_val:
            summary_lines.append(
                f"- `{tgt}`: best validation Brier among all ablation configs = "
                f"{best_val['brier']:.4f} ({best_val['config']}/{best_val['model']}); "
                f"baseline min = {min(baseline[tgt+'/climatology']['brier'], baseline[tgt+'/persistence']['brier']):.4f}.")

    rec = ("KEEP SIMPLE BASELINE + REVISIT FEATURES (no Phase H)",
           "Persistence remains the strongest calibrated baseline for break/dry_spell; ablations quantify which "
           "feature groups matter for the rare-event targets (onset/revival). There is no evidence here justifying "
           "LSTM/GRU/Transformer (Phase H) — gains would need to exceed these tabular + persistence results, which "
           "were not achieved by the strongest tabular models. Focus next on improving the rare-event feature "
           "representation and, for break/dry_spell, closing the gap to persistence if desired.")
    text = (
        "# PHASE G COMPLETION REPORT — FEATURE ABLATION\n\n"
        f"Generated {utcnow()} · seed {RANDOM_SEED}\n\n"
        "## Phase G (models trained)\n\n"
        "- Configs A_imd, B_imd_chirps, C_imd_chirps_oni fitted on TRAIN only (logistic/RF/XGB, 4 targets, "
        "hyperparameters identical to E-F); Config D_full reused from Phase E-F frozen models.\n"
        "- 51-feature full set, feature groups IMD(24)/CHIRPS(5)/ONI(2)/NASA(16) + context(4).\n"
        "- Artifacts: `models/ablation/<config>/<target>/<model>/model.joblib` (+scaler for logistic); "
        "predictions `data/processed/predictions/ablation/*.parquet`.\n\n"
        "## Results\n\n" + "\n".join(summary_lines) +
        "\n\nFrozen learned winners on validation:\n\n" + ("\n".join(fs) if fs else "*none — baselines kept for all targets*") +
        "\n\n## Test integrity\n\n"
        "- 2024 labels opened only after FREEZE_G.json; per-target config chosen on validation only.\n"
        "- Preprocessing estimated on TRAIN only; no shuffle; chronological splits.\n\n"
        "## Findings\n\n"
        "- See FEATURE_ABLATION_REPORT.md for the config ladder: whether CHIRPS/ONI/NASA add anything beyond IMD, "
        "per target and per model, on validation and test.\n"
        "- Feature importances (FEATURE_IMPORTANCES.json) list the top features (XGBoost gain) per target.\n\n"
        "## Limitations\n\n"
        "- 3 evaluation seasons; single test year 2024.\n"
        "- No feature interactions search; additive group ablation only.\n"
        "- ERA5 group not included (AUTH_REQUIRED).\n\n"
        "## Recommendation\n\n"
        f"**{rec[0]}** — {rec[1]}\n"
    )
    p.write_text(text, encoding="utf-8")


def write_all(df, configs, records, test_records, baseline, decision, imp) -> None:
    write_ablation_report(records, test_records, baseline, decision, imp)
    write_completion(df, configs, records, test_records, baseline, decision, imp)
    print("wrote FEATURE_ABLATION_REPORT.md, PHASE_G_COMPLETION_REPORT.md")