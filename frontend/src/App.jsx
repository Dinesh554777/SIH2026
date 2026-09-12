import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import Header from "./components/Header.jsx";
import DemoBanner from "./components/DemoBanner.jsx";
import CellSelector from "./components/CellSelector.jsx";
import ProbabilityCards from "./components/ProbabilityCards.jsx";
import CurrentSignal from "./components/CurrentSignal.jsx";
import Advisory from "./components/Advisory.jsx";
import WhySection from "./components/WhySection.jsx";
import Transparency from "./components/Transparency.jsx";
import Calibration from "./components/Calibration.jsx";
import ErrorPanel from "./components/ErrorPanel.jsx";
import Loading from "./components/Loading.jsx";

export const TARGET_ORDER = ["onset", "break", "revival", "dry_spell"];
const DEMO_CELL = "10.75_77.5";

export default function App() {
  const [cells, setCells] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [metaError, setMetaError] = useState(null);
  const [selCell, setSelCell] = useState(null);
  const [cellInfo, setCellInfo] = useState(null);
  const [date, setDate] = useState("");
  const [lang, setLang] = useState("en");

  const [forecast, setForecast] = useState(null);
  const [explainData, setExplainData] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [advisory, setAdvisory] = useState(null);
  const [detailStatus, setDetailStatus] = useState("idle");
  const [detailError, setDetailError] = useState(null);

  const reqId = useRef(0);

  // Load the cell catalog + model provenance once on mount.
  useEffect(() => {
    let live = true;
    Promise.all([api.cells(), api.modelInfo()])
      .then(([c, m]) => {
        if (!live) return;
        setCells(c.cells);
        setModelInfo(m);
        const fav =
          c.cells.find((x) => x.cell_id === DEMO_CELL) || c.cells[0];
        if (fav) {
          setSelCell(fav.cell_id);
          setCellInfo(fav);
        }
      })
      .catch((e) => {
        if (live) setMetaError(e);
      });
    return () => {
      live = false;
    };
  }, []);

  const loadDetail = useCallback(() => {
    if (!selCell) return;
    const id = ++reqId.current;
    setDetailStatus("loading");
    setDetailError(null);
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
    (modelInfo?.data_mode || forecast?.data_mode || "historical/demo").toLowerCase().includes("historical")
  );

  return (
    <Shell>
      <Header modelInfo={modelInfo} lang={lang} setLang={setLang} />
      <DemoBanner visible={isDemo} />
      <main className="page">
        <CellSelector
          cells={cells}
          selCell={selCell}
          cellInfo={cellInfo}
          date={date}
          onSelectCell={onSelectCell}
          onDateChange={setDate}
        />

        {detailStatus === "error" && (
          <ErrorPanel error={detailError} onRetry={loadDetail} />
        )}

        {detailStatus === "loading" && <Loading label="Requesting forecast…" />}

        {detailStatus === "ready" && (
          <>
            <ProbabilityCards forecast={forecast} advisory={advisory} />
            <CurrentSignal advisory={advisory} />
            <Advisory
              forecast={forecast}
              explanation={explanation}
              advisory={advisory}
            />
            <WhySection explainData={explainData} />
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