import React from 'react';
import { AlertTriangle, Clock } from 'lucide-react';

export default function RiskIndicators({ risk }) {
  const falseOnsetRisk = risk?.false_onset || "Low";
  const drySpellRisk = risk?.dry_spell || "Moderate";
  
  return (
    <div className="re-card">
      <div className="re-card-header">Risk Indicators</div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <div style={{ background: '#fee2e2', borderRadius: '50%', padding: '6px' }}>
            <AlertTriangle size={16} color="#ef4444" />
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#1e293b', fontWeight: '500' }}>False Onset Risk</div>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#10b981' }}>Low</div>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <div style={{ background: '#ffedd5', borderRadius: '50%', padding: '6px' }}>
            <Clock size={16} color="#f97316" />
          </div>
          <div>
            <div style={{ fontSize: '12px', color: '#1e293b', fontWeight: '500' }}>Dry Spell Risk (7 days)</div>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#f59e0b' }}>Moderate</div>
          </div>
        </div>
      </div>
    </div>
  );
}
