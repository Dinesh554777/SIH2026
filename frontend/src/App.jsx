import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import Header from "./components/Header.jsx";
import DemoBanner from "./components/DemoBanner.jsx";
import LocationSelector from "./components/LocationSelector.jsx";
import ScenarioSwitcher from "./components/ScenarioSwitcher.jsx";
import MonsoonStatus from "./components/MonsoonStatus.jsx";
import DecisionPanel from "./components/DecisionPanel.jsx";
import ProbabilityCards from "./components/ProbabilityCards.jsx";
import CurrentSignal from "./components/CurrentSignal.jsx";
import Advisory from "./components/Advisory.jsx";
import WhySection from "./components/WhySection.jsx";
import VillageAdvisoryPanel from "./components/VillageAdvisoryPanel.jsx";
import CellMap from "./components/CellMap.jsx";
import Transparency from "./components/Transparency.jsx";
import Calibration from "./components/Calibration.jsx";
import ErrorPanel from "./components/ErrorPanel.jsx";
import Loading from "./components/Loading.jsx";

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

  const [geography, setGeography] = useState(null);
  const [scenarios, setScenarios] = useState([]);

  const [forecast, setForecast] = useState(null);
  const [explainData, setExplainData] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [advisory, setAdvisory] = useState(null);
  const [decision, setDecision] = useState(null);
  const [detailStatus, setDetailStatus] = useState("idle");
  const [detailError, setDetailError] = useState(null);

  const reqId = useRef(0);
  const didMeta = useRef(false);

  // Load catalog + provenance once; demo geography/scenarios are best-effort.
  useEffect(() => {
    let live = true;
    if (didMeta.current) return;
    didMeta.current = true;
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
      .decision(selCell, date, "paddy")
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
  }, [selCell, date, lang]);

  useEffect(() => {
    loadDetail();
  }, [loadDetail]);

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

  const onScenarioPick = (s) => {
    setDate(s.forecast_date);
    if (s.cell_id) onSelectVillage(village, s.cell_id);
  };

  if (metaError) {
    return (
      <Shell>
        <Header modelInfo={modelInfo} lang={lang} setLang={setLang} />
        <DemoBanner />
        <main className="page">
          <ErrorPanel error={metaError} onRetry={() => window.location.reload()} />
        </main>
      </Shell>
    );
  }

  if (!cells || !selCell) {
    return (
      <Shell>
        <Header modelInfo={modelInfo} lang={lang} setLang={setLang} />
        <DemoBanner />
        <main className="page">
          <Loading label="Loading pilot grid cells…" />
        </main>
      </Shell>
    );
  }

  const isDemo = Boolean(
    (modelInfo?.data_mode || forecast?.data_mode || "historical/demo")
      .toLowerCase()
      .includes("historical")
  );

  return (
    <Shell>
      <Header modelInfo={modelInfo} lang={lang} setLang={setLang} />
      <DemoBanner visible={isDemo} />
      <main className="page">
        <LocationSelector
          geography={geography}
          cells={cells}
          selCell={selCell}
          cellInfo={cellInfo}
          date={date}
          village={village}
          onSelectCell={onSelectCell}
          onSelectVillage={onSelectVillage}
          onDateChange={setDate}
        />

        {detailStatus === "error" && (
          <ErrorPanel error={detailError} onRetry={loadDetail} />
        )}

        {detailStatus === "loading" && <Loading label="Requesting forecast…" />}

        {detailStatus === "ready" && (
          <>
            <ScenarioSwitcher scenarios={scenarios} selCell={selCell} onPick={onScenarioPick} />
            <MonsoonStatus decision={decision} village={village} />
            <ProbabilityCards forecast={forecast} advisory={advisory} />
            <CurrentSignal advisory={advisory} />
            <DecisionPanel decision={decision} village={village} />
            <CellMap cells={cells} selCell={selCell} onSelectCell={onSelectCell} />
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
            />
            <Transparency modelInfo={modelInfo} forecast={forecast} />
            <Calibration forecast={forecast} />
          </>
        )}

        <footer className="footer">
          Pilot grid cells (regular 0.25° grid) are not village/block boundaries.
        </footer>
      </main>
    </Shell>
  );
}

function Shell({ children }) {
  return <div className="app">{children}</div>;
}