import React from 'react';
import { Sprout } from 'lucide-react';

const SUPPORTED_CROPS = [
  { id: 'paddy', name: 'Paddy', icon: '🌾' },
  { id: 'cotton', name: 'Cotton', icon: '☁️' },
  { id: 'maize', name: 'Maize', icon: '🌽' },
];

export default function CropDock({ crop, setCrop }) {
  return (
    <div className="crop-dock">
      <div className="cd-header">
        <Sprout size={16} />
        <span>SELECT CROP SYSTEM</span>
      </div>
      <div className="cd-list">
        {SUPPORTED_CROPS.map(c => (
          <button
            key={c.id}
            className={`cd-btn ${crop === c.id ? 'active' : ''}`}
            onClick={() => setCrop(c.id)}
          >
            <span className="cd-icon">{c.icon}</span>
            <span className="cd-name">{c.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
