import React from "react";
import DemoBanner from "../components/DemoBanner.jsx";
import MapExplorer from "../components/MapExplorer.jsx";
import ScenarioSwitcher from "../components/ScenarioSwitcher.jsx";
import MonsoonStatus from "../components/MonsoonStatus.jsx";
import ProbabilityCards from "../components/ProbabilityCards.jsx";
import CurrentSignal from "../components/CurrentSignal.jsx";
import RiskCards from "../components/RiskCards.jsx";
import DecisionPanel from "../components/DecisionPanel.jsx";
import ForecastTimeline from "../components/ForecastTimeline.jsx";
import CropDock from "../components/crops/CropDock.jsx";
import Advisory from "../components/Advisory.jsx";
import WhySection from "../components/WhySection.jsx";
import VillageAdvisoryPanel from "../components/VillageAdvisoryPanel.jsx";
import Transparency from "../components/Transparency.jsx";
import Calibration from "../components/Calibration.jsx";
import ErrorPanel from "../components/ErrorPanel.jsx";
import Loading from "../components/Loading.jsx";
import CellSelector from "../components/CellSelector.jsx";
import { ISSUED_BY } from "../App.jsx";
import { useLocation } from "react-router-dom";
import { useLanguage } from "../context/LanguageContext.jsx";

export default function Dashboard({
  cells,
  selCell,
  cellInfo,
  date,
  village,
  geography,
  scenarios,
  forecast,
  explainData,
  explanation,
  advisory,
  decision,
  detailStatus,
  detailError,
  modelInfo,
  riskIndex,
  crop,
  setCrop,
  onSelectCell,
  onSelectVillage,
  onDateChange,
  loadDetail,
  isDemo,
}) {
  const location = useLocation();
  const path = location.pathname;
  const { t } = useLanguage();

  if (!cells || !selCell) {
    return (
      <main className="dashboard-layout">
        <Loading label="Loading pilot grid cells…" />
      </main>
    );
  }

  const onScenarioPick = (s) => {
    onDateChange(s.forecast_date);
    if (s.cell_id) onSelectVillage(village, s.cell_id);
  };

  return (
    <main className="dashboard-layout">
      <DemoBanner visible={isDemo} />
      
      <div className="dashboard-workspace">
        <div className="workspace-map">
          <CellSelector
            cells={cells}
            selCell={selCell}
            cellInfo={cellInfo}
            date={date}
            village={village}
            onSelectCell={onSelectCell}
            onDateChange={onDateChange}
          />
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
        </div>

        <div className="workspace-intel">
          {detailStatus === "error" && (
            <ErrorPanel error={detailError} onRetry={loadDetail} />
          )}

          {detailStatus === "loading" && <Loading label={t('common.loading')} />}

          {detailStatus === "ready" && (
            <div className="intel-panels">
              {(path === "/dashboard" || path === "/forecast") && (
                <div id="forecast-section">
                  <ScenarioSwitcher scenarios={scenarios} selCell={selCell} onPick={onScenarioPick} />
                </div>
              )}
              
              {(path === "/dashboard" || path === "/crops") && (
                <CropDock crop={crop} setCrop={setCrop} />
              )}
              
              {(path === "/dashboard" || path === "/crops" || path === "/forecast") && (
                <MonsoonStatus decision={decision} village={village} />
              )}

              {(path === "/dashboard" || path === "/forecast" || path === "/risk") && (
                <ProbabilityCards forecast={forecast} advisory={advisory} />
              )}

              {(path === "/dashboard" || path === "/risk") && (
                <CurrentSignal advisory={advisory} />
              )}

              {(path === "/dashboard" || path === "/risk" || path === "/forecast") && (
                <RiskCards forecast={forecast} advisory={advisory} decision={decision} />
              )}

              {(path === "/dashboard" || path === "/crops") && (
                <DecisionPanel decision={decision} village={village} />
              )}

              {(path === "/dashboard" || path === "/forecast" || path === "/risk") && (
                <ForecastTimeline forecast={forecast} advisory={advisory} decision={decision} />
              )}

              {(path === "/dashboard" || path === "/forecast") && (
                <Advisory
                  forecast={forecast}
                  explanation={explanation}
                  advisory={advisory}
                />
              )}
              
              {(path === "/dashboard" || path === "/forecast") && (
                <WhySection explainData={explainData} />
              )}
              
              {(path === "/dashboard" || path === "/crops") && (
                <VillageAdvisoryPanel
                  cellId={selCell}
                  date={date}
                  decision={decision}
                  village={village}
                  issuedBy={ISSUED_BY}
                  crop={crop}
                />
              )}
              
              {(path === "/dashboard" || path === "/history") && (
                <>
                  <Transparency modelInfo={modelInfo} forecast={forecast} />
                  <Calibration forecast={forecast} />
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
