import React from 'react';
import { CheckSquare, Check } from 'lucide-react';

export default function RecommendedActionsList() {
  return (
    <div className="re-card" style={{ background: '#f0f9ff', border: '1px solid #e0f2fe' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <CheckSquare size={16} color="#0284c7" />
        <div style={{ fontSize: '14px', fontWeight: '700', color: '#0369a1' }}>Recommended Actions</div>
      </div>
      
      <div className="checklist-item">
        <Check size={14} className="checklist-icon" />
        <span>Monitor rainfall for next 2-3 days</span>
      </div>
      <div className="checklist-item">
        <Check size={14} className="checklist-icon" />
        <span>Avoid early sowing</span>
      </div>
      <div className="checklist-item">
        <Check size={14} className="checklist-icon" />
        <span>Prepare for possible dry spell</span>
      </div>
    </div>
  );
}
