import React from 'react';
import { CloudRain, CheckCircle, AlertTriangle, AlertCircle, XCircle } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { motion, AnimatePresence } from 'framer-motion';

export default function MonsoonStatusCard({ forecast }) {
  const { t } = useLanguage();
  
  // Use actual backend data or fallbacks
  const pOnset = forecast?.prediction?.onset_probability ?? null;
  const pDrySpell = forecast?.risk_summary?.dry_spell_prob ?? null;
  const recentRain = forecast?.recent_features?.recent_rainfall_mm ?? null;
  const forecastRain = forecast?.forecast_features?.expected_rainfall_mm ?? null;
  
  // Determine status from probability if status code is not directly provided
  let status = 'UNCERTAIN';
  if (forecast?.prediction?.status) {
    status = forecast.prediction.status;
  } else if (pOnset !== null) {
    if (pOnset > 0.8) status = 'ONSET';
    else if (pOnset > 0.5) status = 'LIKELY';
    else if (pOnset > 0.3) status = 'UNCERTAIN';
    else status = 'LOW';
  }

  const statusConfig = {
    ONSET: { color: 'var(--status-onset)', bg: 'rgba(16, 185, 129, 0.1)', icon: CheckCircle, label: 'ONSET' },
    LIKELY: { color: 'var(--status-likely)', bg: 'rgba(245, 158, 11, 0.1)', icon: AlertCircle, label: 'LIKELY' },
    UNCERTAIN: { color: 'var(--status-uncertain)', bg: 'rgba(249, 115, 22, 0.1)', icon: AlertTriangle, label: 'UNCERTAIN' },
    LOW: { color: 'var(--status-low)', bg: 'rgba(239, 68, 68, 0.1)', icon: XCircle, label: 'LOW' }
  };

  const config = statusConfig[status] || statusConfig.UNCERTAIN;
  const Icon = config.icon;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel" 
      style={{ padding: '20px', marginBottom: '16px' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
        <div style={{ backgroundColor: config.bg, borderRadius: '50%', width: '56px', height: '56px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Icon color={config.color} size={28} />
        </div>
        <div>
          <div style={{ fontSize: '13px', color: 'var(--muted)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Monsoon Status
          </div>
          <div style={{ fontSize: '24px', fontWeight: '800', color: config.color }}>
            {config.label}
          </div>
        </div>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
        <div>
          <div style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: '500' }}>Expected onset:</div>
          <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--ink)' }}>
            {forecast?.prediction?.expected_onset_date ? forecast.prediction.expected_onset_date : 'Data Unavailable'}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: '500' }}>Dry-spell prob:</div>
          <div style={{ fontSize: '14px', fontWeight: '600', color: pDrySpell > 0.4 ? 'var(--status-low)' : 'var(--ink)' }}>
            {pDrySpell !== null ? `${Math.round(pDrySpell * 100)}%` : 'N/A'}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: '500' }}>Recent rainfall:</div>
          <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--ink)' }}>
            {recentRain !== null ? `${recentRain.toFixed(1)} mm` : 'N/A'}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: '500' }}>Forecast rainfall:</div>
          <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--ink)' }}>
            {forecastRain !== null ? `${forecastRain.toFixed(1)} mm` : 'N/A'}
          </div>
        </div>
      </div>

      <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--line)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', fontWeight: '600', color: 'var(--ink)', marginBottom: '8px' }}>
          <span>Confidence</span>
          <span>{pOnset !== null ? `${Math.round(pOnset * 100)}%` : 'Not available'}</span>
        </div>
        <div style={{ height: '8px', backgroundColor: 'var(--line)', borderRadius: '4px', overflow: 'hidden' }}>
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: pOnset !== null ? `${pOnset * 100}%` : '0%' }}
            transition={{ duration: 1, ease: 'easeOut' }}
            style={{ height: '100%', backgroundColor: config.color, borderRadius: '4px' }}
          />
        </div>
      </div>
      
      <div style={{ marginTop: '12px', fontSize: '11px', color: 'var(--muted)', display: 'flex', justifyContent: 'space-between' }}>
        <span>Source: {forecast?.metadata?.source || 'IMD / CHIRPS'}</span>
        <span>Last updated: {forecast?.metadata?.updated_at ? new Date(forecast.metadata.updated_at).toLocaleTimeString() : 'Live'}</span>
      </div>
    </motion.div>
  );
}
