import React from 'react';
import { Home, Map, FileText, FileBarChart, MessageSquare, CloudRain, AlertTriangle, Sprout, History, Bell, Send, Gauge } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext.jsx';

export default function Sidebar() {
  const location = useLocation();
  const { t } = useLanguage();

  const navItems = [
    { path: '/dashboard', icon: Home, label: 'Home' },
    { path: '/forecast', icon: Map, label: 'Map' },
    { path: '/advisory', icon: FileText, label: 'Advisories' },
    { path: '/risk', icon: FileBarChart, label: 'Reports' },
    { path: '/crops', icon: MessageSquare, label: 'Chatbot' },
    // Keeping the rest for navigation purposes but hiding them from main view or separating them
    { path: '/alerts', icon: Bell, label: t('nav.alerts') },
    { path: '/history', icon: History, label: t('nav.history') },
    { path: '/delivery', icon: Send, label: t('nav.delivery') },
    { path: '/command-center', icon: Gauge, label: t('nav.commandCenter') },
  ];

  return (
    <nav style={{
      width: '240px',
      backgroundColor: 'white',
      borderRight: '1px solid #e2e8f0',
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 64px)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: '8px', zIndex: 10 }}>
        {navItems.map((item, idx) => {
          const isActive = location.pathname === item.path || (location.pathname === '/' && item.path === '/dashboard');
          return (
            <Link 
              key={item.path} 
              to={item.path}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 16px',
                borderRadius: '8px',
                textDecoration: 'none',
                color: isActive ? 'white' : '#475569',
                backgroundColor: isActive ? '#0f3a68' : 'transparent',
                fontWeight: isActive ? '600' : '500',
                fontSize: '14px',
                transition: 'all 0.2s',
                marginTop: idx === 5 ? '32px' : '0' // visual separator for extra pages
              }}
            >
              <item.icon size={20} color={isActive ? 'white' : '#475569'} />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </div>

      <div style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', height: '200px', pointerEvents: 'none' }}>
        <svg viewBox="0 0 240 200" fill="none" xmlns="http://www.w3.org/2000/svg">
          {/* Sky gradient */}
          <rect width="240" height="200" fill="url(#paint0_linear)" />
          {/* Hills */}
          <path d="M0 120 Q60 90 120 130 T240 100 L240 200 L0 200 Z" fill="#86efac" opacity="0.6"/>
          <path d="M-20 140 Q80 100 160 150 T260 120 L260 200 L-20 200 Z" fill="#4ade80" opacity="0.8"/>
          <path d="M0 160 Q100 130 180 170 T260 150 L260 200 L0 200 Z" fill="#22c55e" />
          {/* House */}
          <path d="M140 160 L160 160 L160 175 L140 175 Z" fill="#fb923c" />
          <path d="M135 160 L150 150 L165 160 Z" fill="#991b1b" />
          <rect x="145" y="165" width="6" height="10" fill="#78350f" />
          {/* Palm Tree */}
          <path d="M185 175 Q183 160 185 145" stroke="#78350f" strokeWidth="3" fill="none" />
          <path d="M185 145 Q170 145 175 155 M185 145 Q190 135 200 145 M185 145 Q195 145 190 155 M185 145 Q180 135 170 145 M185 145 L185 135" stroke="#166534" strokeWidth="4" strokeLinecap="round" />
          
          <defs>
            <linearGradient id="paint0_linear" x1="120" y1="0" x2="120" y2="200" gradientUnits="userSpaceOnUse">
              <stop stopColor="#e0f2fe" />
              <stop offset="1" stopColor="#bae6fd" />
            </linearGradient>
          </defs>
        </svg>
      </div>
    </nav>
  );
}
