import React from 'react';
import { CloudRain } from 'lucide-react';

export default function MonsoonStatusCard({ forecast }) {
  const pOnset = forecast?.prediction?.onset_probability || 0.72;
  const pct = Math.round(pOnset * 100);
  
  return (
    <div className="re-card monsoon-status-card">
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
        <div style={{ backgroundColor: '#0f766e', borderRadius: '50%', width: '48px', height: '48px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <CloudRain color="white" size={24} />
        </div>
        <div>
          <div style={{ fontSize: '13px', color: '#064e3b', fontWeight: '600' }}>Monsoon Status</div>
          <div style={{ fontSize: '20px', fontWeight: '700', color: '#022c22' }}>Onset Likely</div>
        </div>
      </div>
      
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: '600', color: '#065f46' }}>
          <span>Confidence</span>
          <span>{pct}%</span>
        </div>
        <div className="progress-bar-bg">
          <div className="progress-bar-fill" style={{ width: `${pct}%` }}></div>
        </div>
      </div>
    </div>
  );
}
