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

  return (
    <main style={{ backgroundColor: '#f8fafc', height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
      <div className="dashboard-grid">
        {/* Left Column */}
        <div className="left-panel">
          <div className="re-card" style={{ padding: '12px' }}>
            <LocationSelector
              geography={geography}
              currentLoc={village}
              onSelectLocation={onSelectLocation}
            />
          </div>
          
          {detailStatus === "ready" && (
            <>
              <CurrentAdvisoryCard decision={decision} />
              <QuickInfoCard />
            </>
          )}
        </div>

        {/* Center Column - Map */}
        <div className="center-panel">
          {/* Top Toggles (Mocked for visual parity) */}
          <div className="map-toggles">
            <button className="map-toggle-btn active">{t('dashboardCards.monsoonOnset')}</button>
            <button className="map-toggle-btn">{t('dashboardCards.drySpellRisk')}</button>
            <button className="map-toggle-btn">{t('dashboardCards.rainfall')}</button>
            <button className="map-toggle-btn" style={{ borderRight: 'none' }}>{t('dashboardCards.temperature')}</button>
          </div>
          
          <MapExplorer
            geography={geography}
            cells={cells}
            selCell={selCell}
            cellInfo={cellInfo}
            date={date}
            village={village}
            riskIndex={riskIndex}
            onSelectCell={onSelectCell}
            onSelectVillage={onSelectVillage}
            onDateChange={onDateChange}
          />
          
          {/* Bottom Legend */}
          <div className="map-legend-bottom">
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#0f766e' }}></div> {t('dashboardCards.onset')}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#facc15' }}></div> {t('dashboardCards.likely')}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#fb923c' }}></div> {t('dashboardCards.uncertain')}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ef4444' }}></div> {t('dashboardCards.low')}
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="right-panel">
          {detailStatus === "error" && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>⛅</div>
              <h3 style={{ margin: '0 0 8px 0', color: '#334155' }}>{t('dashboardCards.forecastUnavailable')}</h3>
              <p style={{ margin: '0 0 16px 0', textAlign: 'center', fontSize: '14px' }}>
                {t('dashboardCards.noValidData')}
              </p>
              <button className="btn-primary" onClick={loadDetail}>{t('common.retry')}</button>
            </div>
          )}

          {detailStatus === "loading" && <Loading label={t('dashboardCards.requestingForecast')} />}

          {detailStatus === "ready" && (
            <>
              <MonsoonStatusCard forecast={forecast} />
              <RainfallTrendChart />
              <RiskIndicators risk={forecast?.risk_summary} />
              <RecommendedActionsList />
            </>
          )}
        </div>
      </div>
    </main>
  );
}
