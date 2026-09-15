import React from "react";
import DemoBanner from "../components/DemoBanner.jsx";
import ScenarioSwitcher from "../components/ScenarioSwitcher.jsx";
import ForecastTimeline from "../components/ForecastTimeline.jsx";
import Transparency from "../components/Transparency.jsx";
import Calibration from "../components/Calibration.jsx";
import Loading from "../components/Loading.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";

export default function HistoricalPage({
  cells,
  selCell,
  date,
  village,
  scenarios,
  forecast,
  advisory,
  decision,
  modelInfo,
  detailStatus,
  detailError,
  onDateChange,
  isDemo,
}) {
  const { t } = useLanguage();
  const onScenarioPick = (s) => onDateChange(s.forecast_date);

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
      <h1>Historical analysis</h1>
      <p className="muted">
        Model transparency, calibration metrics, and the past→current forecast
        timeline. Past observations are the only "history" this pilot
        configuration serves — no retrospective bias is assumed.
      </p>

      <ScenarioSwitcher scenarios={scenarios} selCell={selCell} onPick={onScenarioPick} />

      {detailStatus === "loading" && <Loading label={t("common.loading")} />}

      {detailStatus === "ready" && (
        <>
          <ForecastTimeline forecast={forecast} advisory={advisory} decision={decision} />
          <Transparency modelInfo={modelInfo} forecast={forecast} />
          <Calibration forecast={forecast} />
        </>
      )}
    </main>
  );
}
