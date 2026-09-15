import React from "react";
import DemoBanner from "../components/DemoBanner.jsx";
import DecisionPanel from "../components/DecisionPanel.jsx";
import Advisory from "../components/Advisory.jsx";
import WhySection from "../components/WhySection.jsx";
import VillageAdvisoryPanel from "../components/VillageAdvisoryPanel.jsx";
import ErrorPanel from "../components/ErrorPanel.jsx";
import Loading from "../components/Loading.jsx";
import { ISSUED_BY } from "../App.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";

export default function AdvisoryPage({
  cells,
  selCell,
  date,
  village,
  forecast,
  explainData,
  explanation,
  advisory,
  decision,
  detailStatus,
  detailError,
  crop,
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
      <DemoBanner visible={isDemo} />
      <h1>Agricultural advisory</h1>
      <p className="muted">
        Decision-support suggestion for the selected cell: what is happening, why,
        and what the officer should consider next. Advisory is computed
        deterministically from the frozen model output.
      </p>

      {detailStatus === "error" && (
        <ErrorPanel error={detailError} onRetry={loadDetail} />
      )}

      {detailStatus === "loading" && <Loading label={t("common.loading")} />}

      {detailStatus === "ready" && (
        <>
          <DecisionPanel decision={decision} village={village} />
          <Advisory forecast={forecast} explanation={explanation} advisory={advisory} />
          <WhySection explainData={explainData} />
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
