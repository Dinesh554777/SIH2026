const ACTION_VERB = {
  SOW: "Sow",
  WAIT: "Wait — hold sowing",
  MONITOR: "Monitor",
  PREPARE: "Prepare land & inputs",
  IRRIGATION_PREPARE: "Irrigation prepare",
};

export default function DecisionPanel({ decision, village }) {
  if (!decision) return null;
  const evidence = (decision.reasoning ?? []).filter((r) => r.claim);
  const head = evidence.slice(0, 5);
  const support = evidence.slice(5);
  const risk = decision.risk_summary ?? {};

  return (
    <section className="panel decision-panel action-center" id="dashboard">
      <div className="kicker">5 · Agricultural action centre</div>
      <h2>WHAT SHOULD I DO NOW?</h2>
      <div className="decision-card" data-testid="decision-card">
        <div className="decision-card-main">
          <span className="action-badge" data-testid="action-badge">
            {ACTION_VERB[decision.decision] ?? decision.decision}
          </span>
          <p className="decision-explainer">
            {decision.decision_label} for the field area.
            {village && (
              <span className="action-where" data-testid="action-where">
                {" "}
                Recommended at <strong>{village.name}</strong>.
              </span>
            )}
          </p>
        </div>
        <div className="action-reasons">
          <div className="decision-why">
            <h3>Why</h3>
            <ul className="evidence-list">
              {head.map((c, i) => (
                <li key={i} className={c.status ? "ev-pass" : "ev-fail"}>
                  <span className="ev-mark">{c.status ? "✓" : "✕"}</span>
                  <span>
                    {c.claim}
                    {c.detail ? <span className="ev-detail"> — {c.detail}</span> : null}
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div className="decision-risk">
            <h3>How certain?</h3>
            {["onset", "dry_spell", "break"].map((k) => (
              <div key={k} className="risk-row" data-testid={`risk-${k}`}>
                <span className="risk-name">{k.replace("_", " ")}</span>
                <span className="risk-bar">
                  <span
                    className={`risk-fill fill-${risk[k]?.band ?? "low"}`}
                    style={{ width: `${Math.round((risk[k]?.probability ?? 0) * 100)}%` }}
                  />
                </span>
                <span className="risk-val">
                  {Math.round((risk[k]?.probability ?? 0) * 100)}% · {risk[k]?.band}
                </span>
              </div>
            ))}
            <p className="risk-meta">Decision confidence · {decision.confidence}</p>
          </div>
        </div>
        <details className="action-extras" open>
          <summary>Supporting evidence</summary>
          <ul className="evidence-list">
            {support.map((c, i) => (
              <li key={`s-${i}`} className="ev-pass">
                <span className="ev-mark">▸</span>
                <span>{c.claim}</span>
              </li>
            ))}
          </ul>
        </details>
      </div>
      <p className="muted decision-disclaimer">{decision.disclaimer}</p>
    </section>
  );
}