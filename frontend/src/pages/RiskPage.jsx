import React from "react";
import DemoBanner from "../components/DemoBanner.jsx";
import RiskCards from "../components/RiskCards.jsx";
import CurrentSignal from "../components/CurrentSignal.jsx";
import DecisionPanel from "../components/DecisionPanel.jsx";
import ForecastTimeline from "../components/ForecastTimeline.jsx";
import Loading from "../components/Loading.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";

function PriorityLocations({ riskIndex, village }) {
  const { t } = useLanguage();
  if (!riskIndex?.cells) return null;

  const flagged = riskIndex.cells
    .filter((c) => c.risk_level === "critical" || c.risk_level === "high")
    .sort((a, b) => {
      const order = { critical: 0, high: 1, moderate: 2, low: 3 };
      return (order[a.risk_level] ?? 9) - (order[b.risk_level] ?? 9) || (b.hazard_p ?? 0) - (a.hazard_p ?? 0);
    })
    .slice(0, 20);

  if (flagged.length === 0) {
    return (
      <section className="panel">
        <h2>Priority locations</h2>
        <p className="muted">No critical or high-risk cells in the current grid.</p>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="kicker">Priority locations</div>
      <h2>Critical & high-risk cells</h2>
      <p className="muted">
        Cells where the frozen hazard probability crosses the critical (≥0.80) or
        high (≥0.60) threshold. Dominant hazard is the highest individual
        probability.
      </p>
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
          {flagged.map((c) => (
            <tr key={c.cell_id}>
              <td style={{ fontFamily: "monospace", fontWeight: 600 }}>{c.cell_id}</td>
              <td>
                <span className={`risk-badge ${c.risk_level}`}>{c.risk_level}</span>
              </td>
              <td>{c.hazard_p != null ? `${Math.round(c.hazard_p * 100)}%` : "—"}</td>
              <td style={{ textTransform: "capitalize" }}>{(c.dominant_hazard ?? "—").replace("_", " ")}</td>
              <td>{c.decision ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="muted" style={{ marginTop: 8 }}>
        Risk levels derived from the frozen model rule: hazard = max(break, dry_spell);
        critical ≥0.80, high ≥0.60, moderate ≥0.30, low &lt;0.30.
      </p>
    </section>
  );
}

export default function RiskPage({
  cells,
  selCell,
  cellInfo,
  date,
  village,
  forecast,
  advisory,
  decision,
  detailStatus,
  detailError,
  riskIndex,
  onSelectCell,
  onDateChange,
  loadDetail,
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
            <DemoBanner 
        isDemo={isDemo} 
        liveMeta={
          detailError?.detail?.error?.detail ||
          forecast?.live_meta || 
          null
        } 
      />
      <h1>Agricultural risk analysis</h1>
      <p className="muted">
        Overall risk, false-onset, dry-spell, monsoon-break, rainfall deficit and
        priority locations derived from the frozen model probabilities — not
        fabricated estimates.
      </p>

      {detailStatus === "loading" && <Loading label={t("common.loading")} />}

      {detailStatus === "ready" && (
        <>
          <RiskCards forecast={forecast} advisory={advisory} decision={decision} village={village} />
          <CurrentSignal advisory={advisory} />
          <ForecastTimeline forecast={forecast} advisory={advisory} decision={decision} />
          <DecisionPanel decision={decision} village={village} />
        </>
      )}

      <PriorityLocations riskIndex={riskIndex} village={village} />
    </main>
  );
}
