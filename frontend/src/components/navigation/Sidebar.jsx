import React from 'react';
import { Map, CloudRain, AlertTriangle, Sprout, History, Bell } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export default function Sidebar() {
  const location = useLocation();

  const navItems = [
    { path: '/dashboard', icon: Map, label: 'MAP' },
    { path: '/forecast', icon: CloudRain, label: 'FORECAST' },
    { path: '/risk', icon: AlertTriangle, label: 'RISK' },
    { path: '/crops', icon: Sprout, label: 'CROPS' },
    { path: '/history', icon: History, label: 'HISTORY' },
    { path: '/officer', icon: Bell, label: 'ALERTS' },
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
