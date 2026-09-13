import React from 'react';
import { Sprout } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext.jsx';

export default function CropDock({ crop, setCrop }) {
  const { t } = useLanguage();
  const crops = ['paddy', 'cotton', 'maize', 'groundnut'];

  return (
    <div className="crop-dock">
      <div className="cd-header">
        <Sprout size={16} />
        <span>{t('dashboard.cropSystem')}</span>
      </div>
      <div className="cd-list">
        {crops.map((c) => (
          <button
            key={c}
            onClick={() => setCrop(c)}
            className={`cd-btn ${crop === c ? 'active' : ''}`}
          >
            {t(`crops.${c}`) || c}
          </button>
        ))}
      </div>
    </div>
  );
}
