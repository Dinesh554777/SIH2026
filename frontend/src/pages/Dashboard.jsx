import React from "react";
import DemoBanner from "../components/DemoBanner.jsx";
import MapExplorer from "../components/MapExplorer.jsx";
import Loading from "../components/Loading.jsx";
import CellSelector from "../components/CellSelector.jsx";
import ErrorPanel from "../components/ErrorPanel.jsx";

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
  onSelectCell,
  onSelectVillage,
  onDateChange,
  loadDetail,
  isDemo,
}) {
  if (!cells || !selCell) {
    return (
      <main className="dashboard-grid">
        <Loading label="Loading pilot grid cells…" />
      </main>
    );
  }

  return (
    <main style={{ backgroundColor: '#f8fafc', height: 'calc(100vh - 64px)', display: 'flex', flexDirection: 'column' }}>
      <DemoBanner 
        isDemo={isDemo} 
        liveMeta={detailError?.detail?.error?.detail || forecast?.live_meta || null} 
      />
      
      <div className="dashboard-grid">
        {/* Left Column */}
        <div className="left-panel">
          <div className="re-card" style={{ padding: '8px' }}>
            <CellSelector
              cells={cells}
              selCell={selCell}
              cellInfo={cellInfo}
              date={date}
              village={village}
              onSelectCell={onSelectCell}
              onDateChange={onDateChange}
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
            <button className="map-toggle-btn active">Monsoon Onset</button>
            <button className="map-toggle-btn">Dry Spell Risk</button>
            <button className="map-toggle-btn">Rainfall</button>
            <button className="map-toggle-btn" style={{ borderRight: 'none' }}>Temperature</button>
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
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#0f766e' }}></div> Onset
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#facc15' }}></div> Likely
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#fb923c' }}></div> Uncertain
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ef4444' }}></div> Low
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="right-panel">
          {detailStatus === "error" && (
            <ErrorPanel error={detailError} onRetry={loadDetail} />
          )}

          {detailStatus === "loading" && <Loading label="Requesting forecast…" />}

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
