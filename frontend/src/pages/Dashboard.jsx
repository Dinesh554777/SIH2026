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

          {detailStatus === "loading" && <Loading label="Requesting forecast…" />}

          {detailStatus === "ready" && (
            <div className="intel-panels">
              <div id="forecast-section">
                <ScenarioSwitcher scenarios={scenarios} selCell={selCell} onPick={onScenarioPick} />
              </div>
              
              <CropDock crop={crop} setCrop={setCrop} />
              
              <MonsoonStatus decision={decision} village={village} />

              <ProbabilityCards forecast={forecast} advisory={advisory} />

              <CurrentSignal advisory={advisory} />

              <RiskCards forecast={forecast} advisory={advisory} decision={decision} />

              <DecisionPanel decision={decision} village={village} />

              <ForecastTimeline forecast={forecast} advisory={advisory} decision={decision} />

              <Advisory
                forecast={forecast}
                explanation={explanation}
                advisory={advisory}
              />
              
              <WhySection explainData={explainData} />
              
              <VillageAdvisoryPanel
                  cellId={selCell}
                  date={date}
                  decision={decision}
                  village={village}
                  issuedBy={ISSUED_BY}
                  crop={crop}
                />
              
              <Transparency modelInfo={modelInfo} forecast={forecast} />
              <Calibration forecast={forecast} />
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
