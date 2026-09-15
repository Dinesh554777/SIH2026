import { useLanguage } from '../context/LanguageContext.jsx';

export default function DemoBanner({ isDemo = true, liveMeta = null }) {
  const { t } = useLanguage();
  
  if (isDemo) {
    return (
      <div className="demo-banner">
        {t('dashboard.demoBanner')}
      </div>
    );
  }
  
  // Live mode
  if (!liveMeta || liveMeta.status === "UNAVAILABLE") {
    return (
      <div className="demo-banner live-unavailable" style={{ backgroundColor: '#ef4444', color: 'white' }}>
        ⚠️ LIVE DATA UNAVAILABLE 
        {liveMeta?.note ? `: ${liveMeta.note}` : ''}
      </div>
    );
  }
  
  if (liveMeta.status === "STALE") {
    return (
      <div className="demo-banner live-stale" style={{ backgroundColor: '#f59e0b', color: 'white' }}>
        ⚠️ LIVE DATA STALE - USING PREVIOUS DAY
      </div>
    );
  }
  
  return (
    <div className="demo-banner live-active" style={{ backgroundColor: '#10b981', color: 'white' }}>
      🟢 FORECAST ACTIVE (LIVE)
    </div>
  );
}
