import React from 'react';

export default function SystemEvidence({ forecast, decision }) {
  return (
    <div className="glass-panel" style={{ padding: '24px', marginTop: '24px' }}>
      <h3 style={{ fontSize: '16px', marginBottom: '16px', borderBottom: '1px solid var(--line)', paddingBottom: '8px' }}>
        System Evidence & Provenance
      </h3>
      <p style={{ fontSize: '13px', color: 'var(--muted)', marginBottom: '16px' }}>
        Where did this recommendation come from?
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', fontSize: '13px' }}>
        <div style={{ background: 'var(--bg-body)', padding: '12px', borderRadius: '8px' }}>
          <strong style={{ display: 'block', marginBottom: '4px' }}>DATA</strong>
          <div>Source: {forecast?.provenance?.source || 'IMD Grid'}</div>
          <div>Observation Time: {forecast?.forecast_date || 'N/A'}</div>
        </div>

        <div style={{ background: 'var(--bg-body)', padding: '12px', borderRadius: '8px' }}>
          <strong style={{ display: 'block', marginBottom: '4px' }}>PREDICTION</strong>
          <div>Model Version: {forecast?.provenance?.model_version || 'FREEZE_H'}</div>
          <div>Digest: {forecast?.provenance?.freeze_digest?.substring(0,8) || 'N/A'}</div>
        </div>

        <div style={{ background: 'var(--bg-body)', padding: '12px', borderRadius: '8px' }}>
          <strong style={{ display: 'block', marginBottom: '4px' }}>DECISION</strong>
          <div>Thresholds: {decision?.thresholds_version || 'v1.0'}</div>
          <div>Generated At: {forecast?.generated_at || 'N/A'}</div>
        </div>
        
        <div style={{ background: 'var(--bg-body)', padding: '12px', borderRadius: '8px' }}>
          <strong style={{ display: 'block', marginBottom: '4px' }}>SYSTEM MODE</strong>
          <div>Pipeline: {forecast?.data_mode || 'historical'}</div>
          <div>Context: {forecast?.mode || 'live'}</div>
        </div>
      </div>
    </div>
  );
}
