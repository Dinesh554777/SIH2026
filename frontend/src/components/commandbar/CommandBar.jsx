import React, { useState, useEffect } from 'react';
import { Bell, User, MapPin, ChevronDown } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { api } from '../../api.js';

export function Logo({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true" style={{ marginRight: '8px' }}>
      <path d="M24 44C13 34 8 26 8 18a16 16 0 0 1 32 0c0 8-5 16-16 26Z" fill="#16a34a" />
      <path d="M24 20c-3.5-2.5-5-5-5-7a5 5 0 0 1 10 0c0 2-1.5 4.5-5 7Z" fill="#bbf7d0" />
      <path d="M18 26h12M18 30h9" stroke="#14532d" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export default function CommandBar({ breadcrumb }) {
  const { lang, setLang, t } = useLanguage();
  const [liveStatus, setLiveStatus] = useState(null);

  useEffect(() => {
    let active = true;
    const fetchStatus = () => {
      api.liveStatus()
        .then(res => active && setLiveStatus(res))
        .catch(() => {}); // silent fallback
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Check every 30s
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between', 
      padding: '12px 24px', 
      backgroundColor: 'white', 
      borderBottom: '1px solid #e2e8f0',
      height: '64px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}>
          <Logo />
          <span style={{ fontSize: '20px', fontWeight: '800', color: '#0f172a', letterSpacing: '-0.5px' }}>
            AgriMonsoon
          </span>
        </Link>
        <div style={{ height: '32px', width: '1px', backgroundColor: '#e2e8f0' }}></div>
        <span style={{ fontSize: '13px', color: '#64748b', fontWeight: '500', lineHeight: '1.2' }}>
          Hyperlocal Monsoon Intelligence for<br/>Climate-Resilient Agriculture
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', borderRadius: '20px', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', cursor: 'pointer' }}>
          <MapPin size={16} color="#64748b" />
          <select 
            value={lang} 
            onChange={e => setLang(e.target.value)}
            style={{ border: 'none', background: 'transparent', fontSize: '13px', fontWeight: '600', color: '#334155', cursor: 'pointer', outline: 'none', WebkitAppearance: 'none' }}
          >
            <option value="en">Tamil Nadu (EN)</option>
            <option value="ta">Tamil Nadu (TA)</option>
          </select>
          <ChevronDown size={14} color="#64748b" />
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', borderRadius: '20px', backgroundColor: liveStatus?.status === 'ACTIVE' ? '#dcfce7' : liveStatus?.status === 'STALE' ? '#fef08a' : '#fee2e2', border: `1px solid ${liveStatus?.status === 'ACTIVE' ? '#bbf7d0' : liveStatus?.status === 'STALE' ? '#fde047' : '#fecaca'}`, fontSize: '12px', fontWeight: '700', color: liveStatus?.status === 'ACTIVE' ? '#166534' : liveStatus?.status === 'STALE' ? '#854d0e' : '#991b1b' }}>
          <span style={{ fontSize: '16px', lineHeight: '1' }}>●</span>
          <span>{liveStatus?.status === 'ACTIVE' ? 'LIVE FORECAST' : liveStatus?.status === 'STALE' ? 'FORECAST STALE' : 'FORECAST UNAVAILABLE'}</span>
        </div>

        <button style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#64748b' }}>
          <Bell size={20} />
        </button>
        <button style={{ background: '#f1f5f9', border: 'none', cursor: 'pointer', color: '#334155', borderRadius: '50%', width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <User size={18} />
        </button>
      </div>
    </header>
  );
}
