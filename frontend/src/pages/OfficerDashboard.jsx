import React from 'react';
import { AlertTriangle, TrendingUp, Users } from 'lucide-react';

export default function OfficerDashboard() {
  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1e293b', marginBottom: 24 }}>OFFICER COMMAND CENTER</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 24 }}>
        <div style={{ background: '#fff', padding: 20, borderRadius: 8, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ background: '#fee2e2', padding: 12, borderRadius: '50%', color: '#ef4444' }}>
            <AlertTriangle size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>CRITICAL RISK AREAS</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1e293b' }}>12 Villages</div>
          </div>
        </div>

        <div style={{ background: '#fff', padding: 20, borderRadius: 8, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ background: '#dcfce7', padding: 12, borderRadius: '50%', color: '#10b981' }}>
            <TrendingUp size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>ACTIVE ADVISORIES</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1e293b' }}>34 Sent Today</div>
          </div>
        </div>

        <div style={{ background: '#fff', padding: 20, borderRadius: 8, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ background: '#e0f2fe', padding: 12, borderRadius: '50%', color: '#0ea5e9' }}>
            <Users size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 600 }}>FARMERS REACHED</div>
            <div style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1e293b' }}>4,250</div>
          </div>
        </div>
      </div>

      <div style={{ background: '#fff', padding: 24, borderRadius: 8, border: '1px solid #e2e8f0' }}>
        <h2 style={{ fontSize: '1rem', fontWeight: 600, color: '#334155', marginBottom: 16 }}>Priority Action Required</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #f1f5f9' }}>
              <th style={{ padding: '12px 8px', color: '#64748b' }}>Region</th>
              <th style={{ padding: '12px 8px', color: '#64748b' }}>Primary Risk</th>
              <th style={{ padding: '12px 8px', color: '#64748b' }}>Last Advisory</th>
              <th style={{ padding: '12px 8px', color: '#64748b' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
              <td style={{ padding: '12px 8px', fontWeight: 500 }}>Thanjavur Block</td>
              <td style={{ padding: '12px 8px', color: '#ef4444' }}>Dry Spell (High)</td>
              <td style={{ padding: '12px 8px' }}>2 days ago</td>
              <td style={{ padding: '12px 8px' }}><button style={{ background: '#1e293b', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: 4, cursor: 'pointer' }}>Review</button></td>
            </tr>
            <tr style={{ borderBottom: '1px solid #f1f5f9' }}>
              <td style={{ padding: '12px 8px', fontWeight: 500 }}>Orathanadu</td>
              <td style={{ padding: '12px 8px', color: '#eab308' }}>False Onset (Medium)</td>
              <td style={{ padding: '12px 8px' }}>Today</td>
              <td style={{ padding: '12px 8px' }}><button style={{ background: '#1e293b', color: '#fff', border: 'none', padding: '6px 12px', borderRadius: 4, cursor: 'pointer' }}>Review</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
