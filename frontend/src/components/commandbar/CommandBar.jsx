import React, { useState, useEffect } from 'react';
import { Bell, User, MapPin, ChevronDown, Clock, Sun, Moon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext.jsx';
import { api } from '../../api.js';

export function Logo({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true" style={{ marginRight: '8px' }}>
      <path d="M24 44C13 34 8 26 8 18a16 16 0 0 1 32 0c0 8-5 16-16 26Z" fill="var(--primary)" />
      <path d="M24 20c-3.5-2.5-5-5-5-7a5 5 0 0 1 10 0c0 2-1.5 4.5-5 7Z" fill="var(--primary-light)" />
      <path d="M18 26h12M18 30h9" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export default function CommandBar({ breadcrumb }) {
  const { lang, setLang, t } = useLanguage();
  const [liveStatus, setLiveStatus] = useState(null);
  const [theme, setTheme] = useState('light'); // Mock theme state

  useEffect(() => {
    let active = true;
    const fetchStatus = () => {
      api.liveStatus()
        .then(res => active && setLiveStatus(res))
        .catch(() => active && setLiveStatus({ status: 'OFFLINE' })); // Explicit fallback
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Check every 30s
    return () => {
      active = false;
      clearInterval(interval);
    };
  }, []);

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light');
    // Actual implementation would set CSS class on body/html
  };

  const isLive = liveStatus?.status === 'ACTIVE';
  const isOffline = liveStatus?.status === 'OFFLINE' || liveStatus?.status === 'UNAVAILABLE';
  const isDemo = liveStatus?.mode !== 'LIVE' && !isOffline;
  
  let statusText = 'LIVE';
  let statusColor = 'var(--status-onset)';
  let statusBg = 'rgba(16, 185, 129, 0.1)';
  
  if (isOffline) {
    statusText = 'OFFLINE';
    statusColor = 'var(--status-low)';
    statusBg = 'rgba(239, 68, 68, 0.1)';
  } else if (isDemo) {
    statusText = 'DEMO MODE';
    statusColor = 'var(--status-likely)';
    statusBg = 'rgba(245, 158, 11, 0.1)';
  }

  return (
    <header className="glass-panel" style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between', 
      padding: '12px 24px', 
      borderBottom: '1px solid var(--line)',
      height: '64px',
      borderRadius: '0',
      borderTop: 'none',
      borderLeft: 'none',
      borderRight: 'none',
      zIndex: 50,
      position: 'sticky',
      top: 0
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }}>
          <Logo />
          <span style={{ fontSize: '18px', fontWeight: '800', color: 'var(--ink)', letterSpacing: '-0.5px' }}>
            {t('brand.title')}
          </span>
        </Link>
        <div style={{ height: '32px', width: '1px', backgroundColor: 'var(--line)' }}></div>
        
        {/* Selected Location / Breadcrumb */}
        {breadcrumb && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--primary)' }}>
            <MapPin size={18} />
            <span style={{ fontSize: '14px', fontWeight: '600' }}>{breadcrumb}</span>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* Data Timestamp */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--muted)', fontSize: '12px', fontWeight: '500' }}>
          <Clock size={14} />
          <span>Updated: {liveStatus?.last_observation ? new Date(liveStatus.last_observation).toLocaleTimeString() : 'Just now'}</span>
        </div>

        {/* Live Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 10px', borderRadius: '12px', backgroundColor: statusBg, border: `1px solid ${statusColor}40`, fontSize: '12px', fontWeight: '700', color: statusColor }}>
          <span style={{ fontSize: '16px', lineHeight: '1' }}>●</span>
          <span>{statusText}</span>
        </div>

        {/* Language Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <select 
            value={lang} 
            onChange={e => setLang(e.target.value)}
            style={{ border: 'none', background: 'transparent', fontSize: '14px', fontWeight: '600', color: 'var(--ink)', cursor: 'pointer', outline: 'none' }}
          >
            <option value="en">EN</option>
            <option value="ta">TA</option>
            <option value="hi">HI</option>
          </select>
        </div>

        {/* Theme Toggle */}
        <button onClick={toggleTheme} style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--muted)', display: 'flex', alignItems: 'center' }}>
          {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
        </button>

        {/* Notification Icon */}
        <button style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--muted)', display: 'flex', alignItems: 'center' }}>
          <Bell size={20} />
        </button>
        
        {/* User Profile */}
        <button style={{ background: 'var(--accent-soft)', border: 'none', cursor: 'pointer', color: 'var(--accent)', borderRadius: '50%', width: '36px', height: '36px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <User size={18} />
        </button>
      </div>
    </header>
  );
}
