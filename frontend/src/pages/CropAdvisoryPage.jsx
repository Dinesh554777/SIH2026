import React from "react";
import DemoBanner from "../components/DemoBanner.jsx";
import CropDock from "../components/crops/CropDock.jsx";
import MonsoonStatus from "../components/MonsoonStatus.jsx";
import DecisionPanel from "../components/DecisionPanel.jsx";
import RiskCards from "../components/RiskCards.jsx";
import VillageAdvisoryPanel from "../components/VillageAdvisoryPanel.jsx";
import ErrorPanel from "../components/ErrorPanel.jsx";
import Loading from "../components/Loading.jsx";
import { ISSUED_BY } from "../App.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";

export default function CropAdvisoryPage({
  cells,
  selCell,
  date,
  village,
  forecast,
  advisory,
  decision,
  detailStatus,
  detailError,
  crop,
  setCrop,
  loadDetail,
  isDemo,
}) {
  const { t } = useLanguage();

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
      <h1>Crop advisory</h1>
      <p className="muted">
        Select a crop system and view the officer recommendation, risk context
        and last-mile bilingual advisory for the selected cell.
      </p>

      <CropDock crop={crop} setCrop={setCrop} />

      {detailStatus === "error" && (
        <ErrorPanel error={detailError} onRetry={loadDetail} />
      )}

      {detailStatus === "loading" && <Loading label={t("common.loading")} />}

      {detailStatus === "ready" && (
        <>
          <MonsoonStatus decision={decision} village={village} />
          <DecisionPanel decision={decision} village={village} />
          <RiskCards forecast={forecast} advisory={advisory} decision={decision} village={village} />
          <VillageAdvisoryPanel
            cellId={selCell}
            date={date}
            decision={decision}
            village={village}
            issuedBy={ISSUED_BY}
            crop={crop}
          />
        </>
      )}
    </main>
  );
}
