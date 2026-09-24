import React from 'react';

export default function PredictionEvidence({ forecast, decision }) {
  if (!forecast || !decision) return null;

  const factorList = Array.isArray(decision.factors) ? decision.factors : [];
  
  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <h3 style={{ fontSize: '16px', marginBottom: '16px', borderBottom: '1px solid var(--line)', paddingBottom: '8px' }}>
        Why this decision? (Explainability Panel)
      </h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '120px', fontWeight: '600', color: 'var(--muted)' }}>Signals</div>
          <div>➔ {factorList.join(', ') || 'No explicit signals.'}</div>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '120px', fontWeight: '600', color: 'var(--muted)' }}>Prediction</div>
          <div>➔ {forecast?.prediction?.status || 'Unknown'} (Confidence: {forecast?.prediction?.confidence || 'N/A'})</div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '120px', fontWeight: '600', color: 'var(--muted)' }}>Risk</div>
          <div>➔ Dry Spell Probability: {(forecast?.probabilities?.dry_spell * 100).toFixed(1)}%</div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'var(--bg-body)', padding: '8px', borderRadius: '6px' }}>
          <div style={{ width: '112px', fontWeight: '600', color: 'var(--ink)' }}>Final Decision</div>
          <div style={{ fontWeight: 'bold', color: 'var(--primary)' }}>➔ {decision?.action || 'Unknown'}</div>
        </div>
      </div>
    </div>
  );
}
