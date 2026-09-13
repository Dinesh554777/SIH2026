import React from 'react';
import { AlertCircle } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext.jsx';

export default function AgriculturalAction({ decision }) {
  const { t } = useLanguage();
  if (!decision) return null;

  const decisionCode = decision?.decision || decision;

  return (
    <div className="panel agricultural-action">
      <div className="action-header">
        <AlertCircle size={18} className="action-icon" />
        <h2>{t('dashboard.whatShouldIDo')}</h2>
      </div>
      
      <div className="action-card">
        <div className="action-label">{t('dashboard.actionCard')}</div>
        <div className="action-badge" data-testid="action-badge">
          {t(`decisions.${decisionCode}`) || decisionCode}
        </div>
      </div>
    </div>
  );
}
