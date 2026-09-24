import React from 'react';
import { CheckSquare, Check } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function RecommendedActionsList() {
  const { t } = useLanguage();
  return (
    <div className="re-card" style={{ background: '#f0f9ff', border: '1px solid #e0f2fe' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <CheckSquare size={16} color="#0284c7" />
        <div style={{ fontSize: '14px', fontWeight: '700', color: '#0369a1' }}>{t('dashboardCards.recommendedActions')}</div>
      </div>
      
      <div className="checklist-item">
        <Check size={14} className="checklist-icon" />
        <span>{t('dashboardCards.actionMonitor')}</span>
      </div>
      <div className="checklist-item">
        <Check size={14} className="checklist-icon" />
        <span>{t('dashboardCards.actionAvoidSowing')}</span>
      </div>
      <div className="checklist-item">
        <Check size={14} className="checklist-icon" />
        <span>{t('dashboardCards.actionPrepareDry')}</span>
      </div>
    </div>
  );
}
