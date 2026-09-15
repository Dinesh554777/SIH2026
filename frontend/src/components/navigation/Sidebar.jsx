import React from 'react';
import { Map, CloudRain, AlertTriangle, Sprout, History, Bell, FileText, Send, Gauge } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { useLanguage } from '../../context/LanguageContext.jsx';

export default function Sidebar() {
  const location = useLocation();
  const { t } = useLanguage();

  const navItems = [
    { path: '/dashboard', icon: Map, label: t('nav.map') },
    { path: '/forecast', icon: CloudRain, label: t('nav.forecast') },
    { path: '/risk', icon: AlertTriangle, label: t('nav.risk') },
    { path: '/advisory', icon: FileText, label: t('nav.advisory') },
    { path: '/crops', icon: Sprout, label: t('nav.crops') },
    { path: '/alerts', icon: Bell, label: t('nav.alerts') },
    { path: '/history', icon: History, label: t('nav.history') },
    { path: '/delivery', icon: Send, label: t('nav.delivery') },
    { path: '/command-center', icon: Gauge, label: t('nav.commandCenter') },
  ];

  return (
    <nav className="sidebar">
      {navItems.map((item) => (
        <Link 
          key={item.path} 
          to={item.path}
          className={`sidebar-link ${location.pathname === item.path ? 'active' : ''}`}
          title={item.label}
        >
          <item.icon size={24} />
          <span className="sidebar-label">{item.label}</span>
        </Link>
      ))}
    </nav>
  );
}
