import React from 'react';

const BAND_MEANING = {
  low: "Unlikely",
  moderate: "Possible",
  high: "Relatively likely",
  very_high: "Very likely",
};

export default function MonsoonStatus({ decision, village }) {
  if (!decision) return null;

  const fo = decision.false_onset_risk;
  const onset = decision.risk_summary?.onset;
  const onsetPct = Math.round((onset?.probability ?? 0) * 100);

  return (
    <div className="intel-panel" data-testid="status-hero">
      <div className="ip-header">MONSOON INTELLIGENCE</div>
      
      <div className="ip-status-main">
        <div className="ip-status-label">STATUS</div>
        <div className="ip-status-value">{decision.monsoon_status_label}</div>
        <p className="ip-status-desc">
          {decision.critical_reasons?.length ? decision.critical_reasons[0] : ""}
        </p>
        {village && (
          <p className="ip-status-where" data-testid="status-where">
            Service area · <strong>{village.name}</strong>
          </p>
        )}
      </div>

      <div className="ip-grid">
        <div className="ip-grid-item">
          <span className="ip-label">ONSET PROBABILITY</span>
          <span className="ip-value">{onsetPct}%</span>
        </div>
        <div className="ip-grid-item">
          <span className="ip-label">CONFIDENCE</span>
          <span className="ip-value">{decision.confidence}</span>
        </div>
        <div className="ip-grid-item">
          <span className="ip-label">FALSE ONSET RISK</span>
          <span className="ip-value" style={{ textTransform: 'capitalize' }}>{fo ?? "Assessed"}</span>
        </div>
      </div>
    </div>
  );
}