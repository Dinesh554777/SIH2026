import React from 'react';
import { CloudRain, Calendar, Thermometer } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export default function QuickInfoCard() {
  const { t } = useLanguage();
  return (
    <div className="re-card">
      <div className="re-card-header">{t('dashboardCards.quickInfo')}</div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <CloudRain size={20} color="#3b82f6" style={{ marginTop: '2px' }} />
          <div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>{t('dashboardCards.recentRainfall')}</div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b' }}>{t('dashboardCards.last24h')}</div>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <Calendar size={20} color="#10b981" style={{ marginTop: '2px' }} />
          <div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>{t('dashboardCards.nextLikelyRainfall')}</div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b' }}>{t('dashboardCards.in2Days')}</div>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <Thermometer size={20} color="#ef4444" style={{ marginTop: '2px' }} />
          <div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>{t('dashboardCards.avgTemperature')}</div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b' }}>{t('dashboardCards.tempValue')}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
