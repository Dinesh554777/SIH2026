const TARGET_LABEL = {
  onset: "Monsoon onset",
  break: "Break (dry interruption)",
  revival: "Revival",
  dry_spell: "Dry spell",
};

const BAND_CLASS = {
  low: "fill-low",
  moderate: "fill-moderate",
  high: "fill-high",
  very_high: "fill-very-high",
};

export default function ForecastTimeline({ forecast, advisory, decision }) {
  const signal = advisory?.current_signal;
  const past = [
    ["Rain today", signal?.rain_t_mm != null ? `${signal.rain_t_mm} mm` : "—"],
    ["7-day rainfall sum", signal?.sum7_mm != null ? `${signal.sum7_mm} mm` : "—"],
    ["Running dry spell", signal?.dry_streak_days != null ? `${signal.dry_streak_days} day(s)` : "—"],
    ["Wet days in last 7", signal?.wet_days_last7 != null ? `${signal.wet_days_last7}` : "—"],
    ["Regime / trend", signal ? `${signal.rainfall_regime} · ${signal.rainfall_trend}` : "—"],
  ];
  const targets = forecast?.targets ?? {};
  const current = ["onset", "break", "revival", "dry_spell"]
    .filter((t) => targets[t])
    .map((t) => ({
      key: t,
      label: TARGET_LABEL[t],
      pct: Math.round((targets[t].probability ?? 0) * 100),
      band: targets[t].band,
      meaning: targets[t].band_meaning,
    }));

  return (
    <section className="panel timeline-panel" data-testid="forecast-timeline">
      <div className="kicker">6 · Forecast timeline</div>
      <h2>Past → current → what comes next</h2>
      <div className="timeline-grid">
        <div className="timeline-col col-past" data-testid="timeline-past">
          <div className="timeline-col-head">PAST · observed</div>
          <ul className="timeline-list">
            {past.map(([k, v]) => (
              <li key={k}>
                <span className="tl-key">{k}</span>
                <span className="tl-val">{v}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="timeline-col col-current" data-testid="timeline-current">
          <div className="timeline-col-head">CURRENT · model read</div>
          <ul className="timeline-list tl-bars">
            {current.map((c) => (
              <li key={c.key} className="tl-bar-row">
                <span className="tl-key">{c.label}</span>
                <span className="tl-bar">
                  <span
                    className={`tl-fill ${BAND_CLASS[c.band]}`}
                    style={{ width: `${c.pct}%` }}
                  />
                </span>
                <span className="tl-val">
                  {c.pct}% · {c.band}
                </span>
              </li>
            ))}
            {current.length === 0 && <li className="tl-empty">No model read yet.</li>}
          </ul>
        </div>

        <div className="timeline-col col-future" data-testid="timeline-future">
          <div className="timeline-col-head">FUTURE · outlook</div>
          <ul className="timeline-list">
            {["7-day", "14-day", "30-day"].map((h) => (
              <li key={h} className="tl-na">
                <span className="tl-key">{h} outlook</span>
                <span className="tl-val">— not available</span>
              </li>
            ))}
          </ul>
          <p className="tl-note">
            This pilot serves the monsoon state on the <strong>observation date only</strong>.{" "}
            {decision?.confidence ? `Decision confidence: ${decision.confidence}. ` : ""}
            No 7/14/30-day forward horizon is configured. Probabilities describe the
            current day; do not read them as a multi-day forecast.
          </p>
        </div>
      </div>
      <p className="muted">Observed inputs and the frozen model read are kept strictly separate from the (unavailable) forward outlook.</p>
    </section>
  );
}