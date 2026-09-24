import React from 'react';
import { AlertTriangle, Clock } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function RiskIndicators({ risk }) {
  const { t } = useLanguage();
  const falseOnsetRisk = risk?.false_onset || t('dashboardCards.low');
  const drySpellRisk = risk?.dry_spell || t('dashboardCards.moderate');
  
  return (
    <div className="re-card">
      <div className="re-card-header">{t('dashboardCards.riskIndicators')}</div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <div style={{ background: '#fee2e2', borderRadius: '50%', padding: '6px' }}>
            <AlertTriangle size={16} color="#ef4444" />
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#1e293b', fontWeight: '500' }}>{t('dashboardCards.falseOnsetRisk')}</div>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#10b981' }}>{falseOnsetRisk}</div>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <div style={{ background: '#ffedd5', borderRadius: '50%', padding: '6px' }}>
            <Clock size={16} color="#f97316" />
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#1e293b', fontWeight: '500' }}>{t('dashboardCards.drySpellRisk7Days')}</div>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#f59e0b' }}>{drySpellRisk}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
