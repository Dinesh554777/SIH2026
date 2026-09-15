import React from 'react';
import { CloudRain, Calendar, Thermometer } from 'lucide-react';

export default function QuickInfoCard() {
  return (
    <div className="re-card">
      <div className="re-card-header">Quick Info</div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <CloudRain size={20} color="#3b82f6" style={{ marginTop: '2px' }} />
          <div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>Recent Rainfall</div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b' }}>18 mm (last 24h)</div>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <Calendar size={20} color="#10b981" style={{ marginTop: '2px' }} />
          <div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>Next Likely Rainfall</div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b' }}>in 2 days</div>
          </div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
          <Thermometer size={20} color="#ef4444" style={{ marginTop: '2px' }} />
          <div>
            <div style={{ fontSize: '12px', color: '#64748b' }}>Avg. Temperature</div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#1e293b' }}>28°C</div>
          </div>
        </div>
      </div>
    </div>
  );
}
