import React from "react";
import DemoBanner from "../components/DemoBanner.jsx";
import VillageAdvisoryPanel from "../components/VillageAdvisoryPanel.jsx";
import Calibration from "../components/Calibration.jsx";
import Loading from "../components/Loading.jsx";
import { ISSUED_BY } from "../App.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";

export default function DeliveryTracePage({
  cells,
  selCell,
  date,
  village,
  forecast,
  advisory,
  decision,
  detailStatus,
  detailError,
  isDemo,
  crop,
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
      <h1>Advisory delivery &amp; traceability</h1>
      <p className="muted">
        Generate the bilingual village advisory, preview it, and deliver it over
        the supported channels. Every delivery returns a MOCK receipt with
        traceability ids — the gateway is never live.
      </p>

      {detailStatus === "loading" && <Loading label={t("common.loading")} />}

      {detailStatus === "ready" && (
        <>
          <section className="panel">
            <div className="kicker">Delivery pipeline</div>
            <h2>How an advisory reaches the field</h2>
            <p className="muted">
              1. Decision engine computes the action. 2. A deterministic bilingual
              (English + தமிழ்) advisory is generated. 3. The officer selects a
              channel. 4. A MOCK receipt with delivery id is returned. The actual
              gateway is never called in demo/historical mode.
            </p>
          </section>

          <VillageAdvisoryPanel
            cellId={selCell}
            date={date}
            decision={decision}
            village={village}
            issuedBy={ISSUED_BY}
            crop={crop}
          />

          <Calibration forecast={forecast} />
        </>
      )}
    </main>
  );
}
