import React from "react";
import MapExplorer from "../components/MapExplorer.jsx";
import Loading from "../components/Loading.jsx";
import LocationSelector from "../components/LocationSelector.jsx";
import ErrorPanel from "../components/ErrorPanel.jsx";
import { useLanguage } from "../context/LanguageContext";

// New Components
import CurrentAdvisoryCard from "../components/CurrentAdvisoryCard.jsx";
import QuickInfoCard from "../components/QuickInfoCard.jsx";
import MonsoonStatusCard from "../components/MonsoonStatusCard.jsx";
import RainfallTrendChart from "../components/RainfallTrendChart.jsx";
import RiskIndicators from "../components/RiskIndicators.jsx";
import RecommendedActionsList from "../components/RecommendedActionsList.jsx";
import WhatChanged from "../components/WhatChanged.jsx";

export default function Dashboard({
  cells,
  selCell,
  cellInfo,
  date,
  village,
  geography,
  forecast,
  decision,
  detailStatus,
  detailError,
  riskIndex,
  onSelectLocation,
  onSelectCell,
  onSelectVillage,
  onDateChange,
  loadDetail,
  isDemo,
}) {
  const { t } = useLanguage();
  if (!cells || !selCell) {
    return (
      <main className="dashboard-grid">
        <Loading label="Loading pilot grid cells…" />
      </main>
    );
  }

  // To demonstrate the What Changed engine, if backend provides history, use it.
  // Otherwise we pass null and it handles gracefully.
  const previousForecast = forecast?.historical_snapshots ? forecast.historical_snapshots[0] : null;

  return (
    <main style={{ backgroundColor: 'var(--bg)', minHeight: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column', padding: '20px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr 380px', gap: '20px', flex: 1, maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
        {/* Left Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <LocationSelector
            geography={geography}
            currentLoc={village}
            onSelectLocation={onSelectLocation}
          />
          
          {detailStatus === "ready" && (
            <>
              <CurrentAdvisoryCard decision={decision} />
              {/* <QuickInfoCard /> */}
            </>
          )}
        </div>

        {/* Center Column - Map */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          <div className="glass-panel" style={{ flex: 1, position: 'relative', overflow: 'hidden', minHeight: '500px' }}>
            {/* Top Toggles */}
            <div style={{ position: 'absolute', top: '20px', left: '20px', zIndex: 10, display: 'flex', background: 'var(--surface)', borderRadius: '8px', padding: '4px', boxShadow: 'var(--shadow)' }}>
              <button style={{ padding: '6px 12px', borderRadius: '6px', border: 'none', background: 'var(--primary)', color: 'white', fontWeight: '600', fontSize: '13px', cursor: 'pointer' }}>Monsoon Status</button>
              <button style={{ padding: '6px 12px', borderRadius: '6px', border: 'none', background: 'transparent', color: 'var(--muted)', fontWeight: '600', fontSize: '13px', cursor: 'pointer' }}>Rainfall</button>
              <button style={{ padding: '6px 12px', borderRadius: '6px', border: 'none', background: 'transparent', color: 'var(--muted)', fontWeight: '600', fontSize: '13px', cursor: 'pointer' }}>Dry-Spell</button>
            </div>
            
            <MapExplorer
              geography={geography}
              cells={cells}
              selCell={selCell}
              cellInfo={cellInfo}
              date={date}
              village={village}
              riskIndex={riskIndex}
              forecast={forecast}
              decision={decision}
              onSelectCell={onSelectCell}
              onSelectVillage={onSelectVillage}
              onDateChange={onDateChange}
            />
            
            {/* Bottom Legend */}
            <div style={{ position: 'absolute', bottom: '20px', right: '20px', zIndex: 10, background: 'var(--surface)', borderRadius: '8px', padding: '12px', boxShadow: 'var(--shadow)', fontSize: '13px', fontWeight: '600', color: 'var(--ink)' }}>
              <div style={{ marginBottom: '8px', color: 'var(--muted)', fontSize: '11px', textTransform: 'uppercase' }}>Monsoon Status</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--status-onset)' }}></div> Onset
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--status-likely)' }}></div> Likely
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--status-uncertain)' }}></div> Uncertain
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: 'var(--status-low)' }}></div> Low
              </div>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {detailStatus === "error" && (
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 20px', color: 'var(--muted)' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>⛅</div>
              <h3 style={{ margin: '0 0 8px 0', color: 'var(--ink)' }}>{t('dashboardCards.forecastUnavailable')}</h3>
              <p style={{ margin: '0 0 16px 0', textAlign: 'center', fontSize: '14px' }}>
                {t('dashboardCards.noValidData')}
              </p>
              <button style={{ padding: '8px 16px', background: 'var(--primary)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontWeight: '600' }} onClick={loadDetail}>{t('common.retry')}</button>
            </div>
          )}

          {detailStatus === "loading" && (
             <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px' }}>
               <Loading label="Loading forecast..." />
             </div>
          )}

          {detailStatus === "ready" && (
            <>
              <MonsoonStatusCard forecast={forecast} />
              {previousForecast ? (
                <WhatChanged previous={previousForecast} current={forecast} />
              ) : (
                <div className="glass-panel" style={{ padding: '16px', fontSize: '13px', color: 'var(--muted)', textAlign: 'center', marginBottom: '16px' }}>
                  No historical prediction data available for "What Changed" comparison.
                </div>
              )}
              <RainfallTrendChart forecast={forecast} />
              <RiskIndicators risk={forecast?.risk_summary} />
            </>
          )}
        </div>
      </div>
    </main>
  );
}
