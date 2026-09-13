import React from 'react';
import { useLanguage } from '../context/LanguageContext.jsx';

export default function MonsoonStatus({ decision, village }) {
  const { t } = useLanguage();

  if (!decision) return null;

  const fo = decision.false_onset_risk;
  const onset = decision.risk_summary?.onset;
  const onsetPct = Math.round((onset?.probability ?? 0) * 100);

  const BAND_MEANING = {
    low: t('monsoon.unlikely', 'Unlikely'),
    moderate: t('monsoon.possible', 'Possible'),
    high: t('monsoon.relativelyLikely', 'Relatively likely'),
    very_high: t('monsoon.veryLikely', 'Very likely'),
  };

  return (
    <div className="intel-panel" data-testid="status-hero">
      <div className="ip-header">{t('monsoon.intelligence', 'MONSOON INTELLIGENCE')}</div>
      
      <div className="ip-status-main">
        <div className="ip-status-label">{t('monsoon.status', 'STATUS')}</div>
        <div className="ip-status-value">{decision.monsoon_status_label}</div>
        <p className="ip-status-desc">
          {decision.critical_reasons?.length ? decision.critical_reasons[0] : ""}
        </p>
        {village && (
          <p className="ip-status-where" data-testid="status-where">
            {t('monsoon.serviceArea', 'Service area')} · <strong>{village.name}</strong>
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
