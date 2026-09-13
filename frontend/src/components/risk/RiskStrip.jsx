import React from 'react';

const LABEL = {
  onset: "False Onset",
  break: "Monsoon Break",
  dry_spell: "Dry Spell",
};

export default function RiskStrip({ forecast, decision }) {
  if (!forecast || !decision) return null;

  // We map the targets (onset/break/dry_spell) from the forecast
  const risks = ["onset", "dry_spell", "break"].map(t => {
    const tg = forecast.targets?.[t] ?? {};
    let band = tg.band ?? "low";
    // For false onset, we use the decision property
    if (t === "onset" && decision.false_onset_risk) {
      band = decision.false_onset_risk;
    }
    return { id: t, band, label: LABEL[t] };
  });

  return (
    <div className="risk-strip">
      <div className="rs-header">MONSOON RISKS</div>
      <div className="rs-items">
        {risks.map(r => {
          let color = '#10b981'; // low
          if (r.band === 'critical' || r.band === 'high' || r.band === 'very_high') color = '#ef4444';
          else if (r.band === 'moderate' || r.band === 'medium') color = '#eab308';
          
          return (
            <div key={r.id} className="rs-item">
              <span className="rs-label">{r.label}</span>
              <span className="rs-value" style={{ color }}>{r.band.replace('_', ' ')}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
