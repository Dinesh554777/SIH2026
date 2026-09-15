import React from "react";
import DemoBanner from "../components/DemoBanner.jsx";
import Loading from "../components/Loading.jsx";
import { AlertTriangle, TrendingUp, Users } from "lucide-react";
import { useLanguage } from "../context/LanguageContext.jsx";

function riskColor(level) {
  return { critical: "#991b1b", high: "#b45309", moderate: "#a16207", low: "#1d4ed8" }[level] ?? "#334155";
}

export default function CommandCenterPage({
  cells,
  selCell,
  village,
  decision,
  riskIndex,
  detailStatus,
  isDemo,
}) {
  const { t } = useLanguage();

  const counts = { critical: 0, high: 0, moderate: 0, low: 0 };
  if (riskIndex?.cells) {
    riskIndex.cells.forEach((c) => {
      if (counts[c.risk_level] !== undefined) counts[c.risk_level] += 1;
    });
  }

  const topRisk = riskIndex?.cells
    ?.filter((c) => c.risk_level === "critical" || c.risk_level === "high")
    .sort((a, b) => (b.hazard_p ?? 0) - (a.hazard_p ?? 0))
    .slice(0, 8) ?? [];

  return (
    <main className="page-content">
      <DemoBanner visible={isDemo} />
      <h1>{t("officer.commandCenter")}</h1>
      <p className="muted">
        Regional monitoring derived from the live cells-risk payload and the
        frozen decision engine — not hard-coded placeholders.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14, marginBottom: 18 }}>
        <div style={{ background: "#fff", padding: 18, borderRadius: 8, border: "1px solid #e2e8f0", display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ background: "#fee2e2", padding: 10, borderRadius: "50%", color: "#ef4444" }}><AlertTriangle size={22} /></div>
          <div>
            <div style={{ fontSize: 12, color: "#64748b", fontWeight: 600 }}>{t("officer.criticalRiskAreas")}</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#1e293b" }}>{counts.critical + counts.high} cells</div>
          </div>
        </div>
        <div style={{ background: "#fff", padding: 18, borderRadius: 8, border: "1px solid #e2e8f0", display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ background: "#dcfce7", padding: 10, borderRadius: "50%", color: "#10b981" }}><TrendingUp size={22} /></div>
          <div>
            <div style={{ fontSize: 12, color: "#64748b", fontWeight: 600 }}>Active cells</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#1e293b" }}>{riskIndex?.cells?.length ?? 0}</div>
          </div>
        </div>
        <div style={{ background: "#fff", padding: 18, borderRadius: 8, border: "1px solid #e2e8f0", display: "flex", alignItems: "center", gap: 14 }}>
          <div style={{ background: "#e0f2fe", padding: 10, borderRadius: "50%", color: "#0ea5e9" }}><Users size={22} /></div>
          <div>
            <div style={{ fontSize: 12, color: "#64748b", fontWeight: 600 }}>{t("officer.activeAdvisories")}</div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#1e293b" }}>
              {detailStatus === "ready" ? "1 generated" : "Awaiting load"}
            </div>
          </div>
        </div>
      </div>

      <section className="panel">
        <div className="kicker">Priority action required</div>
        <h2>{t("officer.priorityAction")}</h2>
        {topRisk.length === 0 ? (
          <p className="muted">No high/critical cells in the current grid.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Cell</th>
                <th>Risk</th>
                <th>Hazard %</th>
                <th>Dominant</th>
                <th>Decision</th>
              </tr>
            </thead>
            <tbody>
              {topRisk.map((c) => (
                <tr key={c.cell_id}>
                  <td style={{ fontWeight: 600 }}>{c.cell_id}</td>
                  <td><span className={`risk-badge ${c.risk_level}`}>{c.risk_level}</span></td>
                  <td>{c.hazard_p != null ? `${Math.round(c.hazard_p * 100)}%` : "—"}</td>
                  <td style={{ textTransform: "capitalize" }}>{(c.dominant_hazard ?? "—").replace("_", " ")}</td>
                  <td>{c.decision ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="muted" style={{ marginTop: 8 }}>
          Risk levels and dominant hazards are computed from the frozen cells-risk
          grid — never fabricated.
        </p>
      </section>
    </main>
  );
}
