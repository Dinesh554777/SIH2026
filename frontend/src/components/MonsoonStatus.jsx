const TONE = {
  WAIT: "warn",
  SOW: "sow",
  PREPARE: "info",
  MONITOR: "info",
  IRRIGATION_PREPARE: "dry",
};

const BAND_MEANING = {
  low: "Unlikely",
  moderate: "Possible",
  high: "Relatively likely",
  very_high: "Very likely",
};

export default function MonsoonStatus({ decision, village }) {
  if (!decision) return null;
  const tone = TONE[decision.decision] ?? "info";
  const fo = decision.false_onset_risk;
  const foCls = { low: "chip-fo-low", medium: "chip-fo-med", high: "chip-fo-high" }[fo] ?? "";
  const onset = decision.risk_summary?.onset;
  const onsetPct = Math.round((onset?.probability ?? 0) * 100);

  return (
    <section className={`status-hero tone-${tone}`} data-testid="status-hero">
      <div className="status-hero-inner">
        <div className="status-copy">
          <div className="kicker light">2 · Current monsoon status</div>
          <h2 className="status-title">{decision.monsoon_status_label}</h2>
          <p className="status-sub">
            {decision.critical_reasons?.length
              ? decision.critical_reasons[0]
              : "Field-level overview for the selected location."}
          </p>
          {village && (
            <p className="status-where" data-testid="status-where">
              Service area · <strong>{village.name}</strong>
            </p>
          )}
          <div className="status-chips">
            <span className={`chip chip-fo ${foCls}`}>
              False-onset risk · {fo ?? "assessed"}
            </span>
            <span className="chip">Confidence · {decision.confidence}</span>
            <span className="chip">Rules · v{decision.thresholds_version}</span>
            <span className="chip">Data · historical/demo</span>
          </div>
        </div>
        <div className="status-decision">
          <div className="decision-chip" data-testid="decision-chip">
            <span className="decision-verb">{decision.decision}</span>
            <span className="decision-label">{decision.decision_label}</span>
          </div>
          <p className="decision-hint">{decision.explanation}</p>
        </div>
      </div>
      <div className="status-outlook" data-testid="status-outlook">
        <div className="outlook-item">
          <span className="outlook-label">Onset outlook</span>
          <span className="outlook-value">
            {BAND_MEANING[onset?.band] ?? "Not yet indicated"} ({onsetPct}%)
          </span>
        </div>
        <div className="outlook-item">
          <span className="outlook-label">Next review</span>
          <span className="outlook-value">daily (or on next rainfall event)</span>
        </div>
        <div className="outlook-item">
          <span className="outlook-label">Status basis</span>
          <span className="outlook-value">same-day observations only</span>
        </div>
      </div>
    </section>
  );
}