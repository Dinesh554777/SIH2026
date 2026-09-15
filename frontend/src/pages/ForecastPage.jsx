import React from "react";
import DemoBanner from "../components/DemoBanner.jsx";
import MonsoonStatus from "../components/MonsoonStatus.jsx";
import ProbabilityCards from "../components/ProbabilityCards.jsx";
import CurrentSignal from "../components/CurrentSignal.jsx";
import ForecastTimeline from "../components/ForecastTimeline.jsx";
import Advisory from "../components/Advisory.jsx";
import WhySection from "../components/WhySection.jsx";
import ScenarioSwitcher from "../components/ScenarioSwitcher.jsx";
import CellSelector from "../components/CellSelector.jsx";
import ErrorPanel from "../components/ErrorPanel.jsx";
import Loading from "../components/Loading.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";

export default function ForecastPage({
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
  onSelectCell,
  onDateChange,
  loadDetail,
  isDemo,
}) {
  const { t } = useLanguage();
  const onScenarioPick = (s) => {
    onDateChange(s.forecast_date);
  };

  if (!cells || !selCell) {
    return (
      <main className="page-content">
        <Loading label={t("common.loading")} />
      </main>
    );
  }

  return (
    <main className="page-content">
            <DemoBanner 
        isDemo={isDemo} 
        liveMeta={
          detailError?.detail?.error?.detail ||
          forecast?.live_meta || 
          null
        } 
      />
      <h1>Forecast workspace</h1>
      <p className="muted">
        Onset prediction, expected rainfall, timeline and honest outlook for the
        selected cell. The forecast is a frozen model read, not a multi-day
        projection.
      </p>

      <CellSelector
        cells={cells}
        selCell={selCell}
        cellInfo={cellInfo}
        date={date}
        village={village}
        onSelectCell={onSelectCell}
        onDateChange={onDateChange}
      />

      {detailStatus === "error" && (
        <ErrorPanel error={detailError} onRetry={loadDetail} />
      )}

      {detailStatus === "loading" && <Loading label={t("common.loading")} />}

      {detailStatus === "ready" && (
        <>
          <ScenarioSwitcher
            scenarios={scenarios}
            selCell={selCell}
            onPick={onScenarioPick}
          />
          <MonsoonStatus decision={decision} village={village} />
          <ProbabilityCards forecast={forecast} advisory={advisory} />
          <CurrentSignal advisory={advisory} />
          <ForecastTimeline forecast={forecast} advisory={advisory} decision={decision} />
          <Advisory forecast={forecast} explanation={explanation} advisory={advisory} />
          <WhySection explainData={explainData} />
        </>
      )}
    </main>
  );
}
