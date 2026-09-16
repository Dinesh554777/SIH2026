import React from 'react';
import { Sprout } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function CurrentAdvisoryCard({ decision }) {
  const { t } = useLanguage();
  // If decision is not available, we can mock it based on the screenshot
  const actionText = decision?.code || "WAIT";
  
  return (
    <div className="re-card advisory-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#065f46', fontWeight: '600' }}>
        <Sprout size={18} />
        <span>{t('dashboardCards.currentAdvisory')}</span>
      </div>
      
      <div className="advisory-btn">
        {actionText.replace(/_/g, ' ')}
      </div>
      
      <p style={{ fontSize: '13px', color: '#064e3b', margin: 0, lineHeight: '1.4' }}>
        {t('dashboardCards.sowingRecommended')}
      </p>
    </div>
  );
}
