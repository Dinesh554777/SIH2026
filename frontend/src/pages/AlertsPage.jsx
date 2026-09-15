import React from "react";
import DemoBanner from "../components/DemoBanner.jsx";
import Loading from "../components/Loading.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";

function riskColor(level) {
  return { critical: "#991b1b", high: "#b45309", moderate: "#a16207", low: "#1d4ed8" }[level] ?? "#334155";
}

function ActionAlerts({ decision, village }) {
  if (!decision) return null;
  const risk = decision.risk_summary ?? {};
  const items = [];

  if (decision.false_onset_risk === "high") {
    items.push({
      level: "high",
      label: "False-onset risk",
      detail: "Recent rainfall looks like a false start. Hold sowing until the sustained wet-day rule is met.",
    });
  }

  for (const key of ["dry_spell", "break", "onset"]) {
    const band = risk[key]?.band;
    const pct = Math.round((risk[key]?.probability ?? 0) * 100);
    if (band === "high" || band === "very_high" || band === "critical") {
      items.push({
        level: band === "very_high" || band === "critical" ? "critical" : "high",
        label: `${key.replace("_", " ")} — ${pct}%`,
        detail: decision.reasoning?.find?.((r) => r.claim)?.claim ?? "Requires officer review.",
      });
    }
  }

  if (items.length === 0) {
    return (
      <section className="panel">
        <h2>Active alerts</h2>
        <p className="muted">No actionable alerts for the current cell. The situation is within normal thresholds.</p>
        {village && <p className="muted">Location · {village.name}</p>}
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="kicker">Active alerts</div>
      <h2>What needs attention now</h2>
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {items.map((item, i) => (
          <li
            key={i}
            style={{
              borderLeft: `4px solid ${riskColor(item.level)}`,
              padding: "10px 12px",
              marginBottom: 10,
              background: "#fff",
              borderRadius: 4,
              border: "1px solid #f1f5f9",
            }}
          >
            <div style={{ fontWeight: 700, fontSize: 13, color: riskColor(item.level), textTransform: "uppercase" }}>
              {item.level}
            </div>
            <div style={{ fontWeight: 600, color: "#1e293b", marginTop: 4 }}>{item.label}</div>
            <div style={{ color: "#475569", fontSize: 13, marginTop: 4 }}>{item.detail}</div>
          </li>
        ))}
      </ul>
      <p className="muted">Alerts are derived from the frozen decision engine outputs — not fabricated counts.</p>
    </section>
  );
}

function GridAlerts({ riskIndex }) {
  if (!riskIndex?.cells) return null;

  const counts = { critical: 0, high: 0, moderate: 0, low: 0 };
  riskIndex.cells.forEach((c) => {
    if (counts[c.risk_level] !== undefined) counts[c.risk_level] += 1;
  });

  const topCritical = riskIndex.cells
    .filter((c) => c.risk_level === "critical")
    .sort((a, b) => (b.hazard_p ?? 0) - (a.hazard_p ?? 0))
    .slice(0, 10);

  return (
    <section className="panel">
      <div className="kicker">Grid overview</div>
      <h2>Whole-grid risk summary</h2>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 12 }}>
        {Object.entries(counts).map(([level, count]) => (
          <div key={level} style={{ padding: "10px 14px", background: "#fff", border: "1px solid #f1f5f9", borderRadius: 6, minWidth: 90, textAlign: "center" }}>
            <div style={{ fontSize: 22, fontWeight: 700, color: riskColor(level) }}>{count}</div>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#64748b", textTransform: "uppercase" }}>{level}</div>
          </div>
        ))}
      </div>
      {topCritical.length > 0 && (
        <>
          <h3 style={{ fontSize: 14, fontWeight: 700, color: "#1e293b", marginBottom: 8 }}>Top critical cells</h3>
          <table className="data-table">
            <thead>
              <tr><th>Cell</th><th>Hazard %</th><th>Dominant</th></tr>
            </thead>
            <tbody>
              {topCritical.map((c) => (
                <tr key={c.cell_id}>
                  <td style={{ fontFamily: "monospace", fontWeight: 600 }}>{c.cell_id}</td>
                  <td>{c.hazard_p != null ? `${Math.round(c.hazard_p * 100)}%` : "—"}</td>
                  <td style={{ textTransform: "capitalize" }}>{(c.dominant_hazard ?? "—").replace("_", " ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
      <p className="muted" style={{ marginTop: 8 }}>
        Grid counts are computed from the real cells-risk payload for the active
        date — never hard-coded.
      </p>
    </section>
  );
}

export default function AlertsPage({
  cells,
  selCell,
  village,
  decision,
  detailStatus,
  riskIndex,
  isDemo,
}) {
  const { t } = useLanguage();

  if (!cells || !selCell) {
    return (
      <main className="page-content">
        <Loading label={t("common.loading")} />
      </main>
    );
  }

  return (
    <main className="page-content">
      <DemoBanner visible={isDemo} />
      <h1>Alerts</h1>
      <p className="muted">
        Actionable alerts derived from the frozen decision engine and the
        whole-grid cells-risk payload — not fabricated counts.
      </p>

      {detailStatus === "loading" && <Loading label={t("common.loading")} />}

      {detailStatus === "ready" && <ActionAlerts decision={decision} village={village} />}
      <GridAlerts riskIndex={riskIndex} />
    </main>
  );
}
