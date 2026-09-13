import React from 'react';
import { useLanguage } from '../../context/LanguageContext.jsx';

export default function RiskStrip({ forecast, decision }) {
  const { t } = useLanguage();
  if (!forecast || !decision) return null;

  const getLabel = (target) => t(`risk.${target}`);
  
  // We map the targets (onset/break/dry_spell) from the forecast
  const risks = ["onset", "dry_spell", "break"].map(tTarget => {
    const tg = forecast.targets?.[tTarget] ?? {};
    
    // Very naive mapping for the UI: derive High/Medium/Low based on output
    let level = 'low';
    if (tg.probability > 0.7) level = 'critical';
    else if (tg.probability > 0.5) level = 'high';
    else if (tg.probability > 0.3) level = 'medium';

    const probFmt = tg.probability != null 
      ? (tg.probability * 100).toFixed(1) + "%" 
      : "--%";

    return {
      key: tTarget,
      label: getLabel(tTarget),
      level,
      probability: probFmt
    };
  });

  return (
    <section className="panel risk-strip" data-testid="risk-legend">
      <div className="rs-header">
        <h2>{t('risk.legendTitle')}</h2>
        <span className="rs-subtitle">
          {t('risk.legendDerived')} · {forecast.date}
        </span>
      </div>

      <div className="rs-cards" data-testid="risk-cards">
        {risks.map(r => (
          <div key={r.key} className={`rs-card level-${r.level}`} data-testid={`risk-card-${r.key.replace('_', '-')}`}>
            <div className="rs-card-val">{r.probability}</div>
            <div className="rs-card-label">{r.label}</div>
            <div className="rs-card-badge">{t(`risk.${r.level}`) || r.level}</div>
          </div>
        ))}
      </div>
    </section>
  );
}
