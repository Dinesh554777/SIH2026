export default function ScenarioSwitcher({ scenarios, selCell, onPick }) {
  if (!scenarios || scenarios.length === 0) return null;
  return (
    <section className="panel scenario-strip" data-testid="scenario-strip">
      <div className="kicker">Demo walkthrough</div>
      <h2>Frozen pilot scenarios</h2>
      <p className="muted">
        Each chip replays a real date from the frozen blueprint on cell{" "}
        <strong>{selCell}</strong> — the decision is recomputed deterministically, never
        hard-coded.
      </p>
      <div className="scenario-list">
        {scenarios.map((s) => (
          <button
            key={s.id}
            className="scenario-chip"
            data-testid="scenario-chip"
            onClick={() => onPick(s)}
          >
            <span className="sc-date">{s.forecast_date}</span>
            <span className="sc-decision">{s.decision?.decision ?? "…"}</span>
            <span className="sc-note">{s.note}</span>
          </button>
        ))}
      </div>
    </section>
  );
}