import { useCallback, useEffect, useRef, useState } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { api } from "./api.js";

import CommandBar from "./components/commandbar/CommandBar.jsx";
import Sidebar from "./components/navigation/Sidebar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import OfficerDashboard from "./pages/OfficerDashboard.jsx";
import ErrorPanel from "./components/ErrorPanel.jsx";

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
  const [lang, setLang] = useState("en");
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
        <CommandBar breadcrumb="Error" lang={lang} setLang={setLang} />
        <div className="app-body">
          <ErrorPanel error={metaError} onRetry={() => window.location.reload()} />
        </div>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <CommandBar breadcrumb={breadcrumbStr} lang={lang} setLang={setLang} />
      
      <div className="app-body">
        <Sidebar />
        
        <div className="app-content">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route
              path="/dashboard"
              element={
                <Dashboard
                  cells={cells}
                  selCell={selCell}
                  cellInfo={cellInfo}
                  date={date}
                  village={village}
                  geography={geography}
                  scenarios={scenarios}
                  forecast={forecast}
                  explainData={explainData}
                  explanation={explanation}
                  advisory={advisory}
                  decision={decision}
                  detailStatus={detailStatus}
                  detailError={detailError}
                  modelInfo={modelInfo}
                  crop={crop}
                  setCrop={setCrop}
                  onSelectCell={onSelectCell}
                  onSelectVillage={onSelectVillage}
                  onDateChange={setDate}
                  loadDetail={loadDetail}
                  riskIndex={cellsRisk}
                  isDemo={isDemo}
                />
              }
            />
            <Route
              path="/forecast"
              element={<Dashboard cells={cells} selCell={selCell} cellInfo={cellInfo} date={date} village={village} geography={geography} scenarios={scenarios} forecast={forecast} explainData={explainData} explanation={explanation} advisory={advisory} decision={decision} detailStatus={detailStatus} detailError={detailError} modelInfo={modelInfo} crop={crop} setCrop={setCrop} onSelectCell={onSelectCell} onSelectVillage={onSelectVillage} onDateChange={setDate} loadDetail={loadDetail} riskIndex={cellsRisk} isDemo={isDemo} />}
            />
            <Route
              path="/risk"
              element={<Dashboard cells={cells} selCell={selCell} cellInfo={cellInfo} date={date} village={village} geography={geography} scenarios={scenarios} forecast={forecast} explainData={explainData} explanation={explanation} advisory={advisory} decision={decision} detailStatus={detailStatus} detailError={detailError} modelInfo={modelInfo} crop={crop} setCrop={setCrop} onSelectCell={onSelectCell} onSelectVillage={onSelectVillage} onDateChange={setDate} loadDetail={loadDetail} riskIndex={cellsRisk} isDemo={isDemo} />}
            />
            <Route
              path="/crops"
              element={<Dashboard cells={cells} selCell={selCell} cellInfo={cellInfo} date={date} village={village} geography={geography} scenarios={scenarios} forecast={forecast} explainData={explainData} explanation={explanation} advisory={advisory} decision={decision} detailStatus={detailStatus} detailError={detailError} modelInfo={modelInfo} crop={crop} setCrop={setCrop} onSelectCell={onSelectCell} onSelectVillage={onSelectVillage} onDateChange={setDate} loadDetail={loadDetail} riskIndex={cellsRisk} isDemo={isDemo} />}
            />
            <Route
              path="/history"
              element={<Dashboard cells={cells} selCell={selCell} cellInfo={cellInfo} date={date} village={village} geography={geography} scenarios={scenarios} forecast={forecast} explainData={explainData} explanation={explanation} advisory={advisory} decision={decision} detailStatus={detailStatus} detailError={detailError} modelInfo={modelInfo} crop={crop} setCrop={setCrop} onSelectCell={onSelectCell} onSelectVillage={onSelectVillage} onDateChange={setDate} loadDetail={loadDetail} riskIndex={cellsRisk} isDemo={isDemo} />}
            />
            <Route path="/officer" element={<OfficerDashboard />} />
            <Route path="*" element={<PlaceholderPage />} />
          </Routes>
        </div>
      </div>
    </div>
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