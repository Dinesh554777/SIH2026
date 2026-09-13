import React from 'react';
import { Search, Bell, User } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function CommandBar({ breadcrumb, lang, setLang }) {
  return (
    <header className="command-bar">
      <h1 className="sr-only">Hyperlocal Monsoon Decision Support</h1>
      <div className="cb-brand">
        <Link to="/" className="cb-logo-link">
          <span className="cb-logo">🌾</span>
          <span className="cb-title">AGRI-MONSOON</span>
        </Link>
        <span className="cb-tagline">Probabilistic agricultural decision support</span>
      </div>

      <div className="cb-breadcrumb">
        {breadcrumb || "Select Location"}
      </div>

      <div className="cb-actions">
        <button className="cb-action-btn" title="Search">
          <Search size={18} />
        </button>
        <button className="cb-action-btn" title="Alerts">
          <Bell size={18} />
        </button>
        
        <div className="cb-lang-toggle">
          <button 
            className={`cb-lang-btn ${lang === 'en' ? 'active' : ''}`}
            onClick={() => setLang('en')}
          >
            EN
          </button>
          <span className="cb-lang-div">|</span>
          <button 
            className={`cb-lang-btn ${lang === 'ta' ? 'active' : ''}`}
            onClick={() => setLang('ta')}
          >
            தமிழ்
          </button>
        </div>

        <button className="cb-action-btn" title="Profile">
          <User size={18} />
        </button>
      </div>
    </header>
  );
}
