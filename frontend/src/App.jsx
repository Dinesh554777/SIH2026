import { useCallback, useEffect, useRef, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { api } from "./api.js";

import AppLayout from "./pages/AppLayout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import ForecastPage from "./pages/ForecastPage.jsx";
import RiskPage from "./pages/RiskPage.jsx";
import AdvisoryPage from "./pages/AdvisoryPage.jsx";
import CropAdvisoryPage from "./pages/CropAdvisoryPage.jsx";
import AlertsPage from "./pages/AlertsPage.jsx";
import HistoricalPage from "./pages/HistoricalPage.jsx";
import DeliveryTracePage from "./pages/DeliveryTracePage.jsx";
import CommandCenterPage from "./pages/CommandCenterPage.jsx";
import ErrorPanel from "./components/ErrorPanel.jsx";
import { useLanguage } from "./context/LanguageContext.jsx";

export const TARGET_ORDER = ["onset", "break", "revival", "dry_spell"];
const DEMO_CELL = "10.75_77.5";
export const ISSUED_BY = "Officer (Dinesh)";

export default function App() {
  const [cells, setCells] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [metaError, setMetaError] = useState(null);
  const [selCell, setSelCell] = useState(null);
  const [cellInfo, setCellInfo] = useState(null);
  const [village, setVillage] = useState(null);
  const [date, setDate] = useState("");
  const { lang } = useLanguage();
  const [crop, setCrop] = useState("paddy");

  const [geography, setGeography] = useState(null);
  const [scenarios, setScenarios] = useState([]);

  const [forecast, setForecast] = useState(null);
  const [explainData, setExplainData] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [advisory, setAdvisory] = useState(null);
  const [decision, setDecision] = useState(null);
  const [cellsRisk, setCellsRisk] = useState(null);
  const [detailStatus, setDetailStatus] = useState("idle");
  const [detailError, setDetailError] = useState(null);

  const reqId = useRef(0);

  useEffect(() => {
    let live = true;
    Promise.all([api.cells(), api.modelInfo()])
      .then(([c, m]) => {
        if (!live) return;
        setCells(c.cells);
        setModelInfo(m);
        const fav = c.cells.find((x) => x.cell_id === DEMO_CELL) || c.cells[0];
        if (fav) {
          setSelCell(fav.cell_id);
          setCellInfo(fav);
        }
      })
      .catch((e) => {
        if (live) setMetaError(e);
      });
    api
      .geographyDemo()
      .then((g) => live && setGeography(g))
      .catch(() => live && setGeography(null));
    api
      .scenarios()
      .then((s) => live && setScenarios(s.scenarios ?? []))
      .catch(() => live && setScenarios([]));
    return () => {
      live = false;
    };
  }, []);

  const loadDetail = useCallback(() => {
    if (!selCell) return;
    const id = ++reqId.current;
    setDetailStatus("loading");
    setDetailError(null);
    api
      .decision(selCell, date, crop)
      .then((r) => {
        if (reqId.current === id) setDecision(r.decision ?? r);
      })
      .catch(() => {
        if (reqId.current === id) setDecision(null);
      });
    Promise.all([
      api.forecast(selCell, date),
      api.explain(selCell, date),
      api.explanation(selCell, date, lang),
      api.advisory(selCell, date),
    ])
      .then(([f, ex, eo, adv]) => {
        if (reqId.current !== id) return;
        setForecast(f);
        setExplainData(ex);
        setExplanation(eo);
        setAdvisory(adv);
        setDetailStatus("ready");
      })
      .catch((err) => {
        if (reqId.current !== id) return;
        setDetailError(err);
        setDetailStatus("error");
      });
  }, [selCell, date, lang, crop]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

  useEffect(() => {
    let live = true;
    api
      .cellsRisk(date)
      .then((r) => live && setCellsRisk(r))
      .catch(() => live && setCellsRisk(null));
    return () => {
      live = false;
    };
  }, [date]);

  const onSelectCell = (cellId) => {
    setSelCell(cellId);
    setCellInfo((cells || []).find((c) => c.cell_id === cellId) || null);
    setVillage(null);
  };

  const onSelectVillage = (villageObj, cellId) => {
    setVillage(villageObj);
    setSelCell(cellId);
    setCellInfo((cells || []).find((c) => c.cell_id === cellId) || null);
  };

  const onSelectLocation = (loc) => {
    setVillage(loc);
    setSelCell(loc.cell_id);
    setCellInfo((cells || []).find((c) => c.cell_id === loc.cell_id) || null);
  };

  const isDemo = Boolean(
    (modelInfo?.data_mode || forecast?.data_mode || "historical/demo")
      .toLowerCase()
      .includes("historical")
  );

  let breadcrumbStr = "";
  if (village) {
    const d = village.district?.district?.name ?? village.district?.name ?? "";
    const bl = village.block?.block?.name ?? village.block?.name ?? "";
    const st = village.state?.name ?? village.state ?? "";
    breadcrumbStr = [st, d, bl, village.village_name ?? village.name].filter(Boolean).join(" / ");
    if (!breadcrumbStr) breadcrumbStr = village.village_id ?? String(village.cell_id ?? "");
  }

  if (metaError) {
    return (
      <div className="app-shell">
        <ErrorPanel error={metaError} onRetry={() => window.location.reload()} />
      </div>
    );
  }

  const pageProps = {
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
    riskIndex: cellsRisk,
    crop,
    setCrop,
    onSelectCell,
    onSelectVillage,
    onSelectLocation,
    onDateChange: setDate,
    loadDetail,
    isDemo,
  };

  return (
    <Routes>
      <Route element={<AppLayout breadcrumb={breadcrumbStr} />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard {...pageProps} />} />
        <Route path="/forecast" element={<ForecastPage {...pageProps} />} />
        <Route path="/risk" element={<RiskPage {...pageProps} />} />
        <Route path="/advisory" element={<AdvisoryPage {...pageProps} />} />
        <Route path="/crops" element={<CropAdvisoryPage {...pageProps} />} />
        <Route path="/alerts" element={<AlertsPage {...pageProps} />} />
        <Route path="/history" element={<HistoricalPage {...pageProps} />} />
        <Route path="/historical" element={<HistoricalPage {...pageProps} />} />
        <Route path="/delivery" element={<DeliveryTracePage {...pageProps} />} />
        <Route path="/officer" element={<CommandCenterPage {...pageProps} />} />
        <Route path="/command-center" element={<CommandCenterPage {...pageProps} />} />
        <Route path="*" element={<PlaceholderPage />} />
      </Route>
    </Routes>
  );
}

function PlaceholderPage() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
      <div style={{ fontSize: '3rem', marginBottom: '16px' }}>🚧</div>
      <h2>Module Under Construction</h2>
      <p>This section is scheduled for development in a future phase.</p>
    </div>
  );
}