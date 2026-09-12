const BAND_COLOR = {
  low: "#1d4ed8",
  moderate: "#ca8a04",
  high: "#d97706",
  very_high: "#b91c1c",
};

const LABEL = {
  onset: "Monsoon Onset",
  break: "Monsoon Break",
  revival: "Revival",
  dry_spell: "Dry Spell",
};

const SHORT = {
  onset: "Monsoon onset is not yet indicated.",
  break: "A dry interruption is likely.",
  revival: "Rainfall revival is plausible.",
  dry_spell: "Near-term dry conditions are likely.",
};

function pct(value, digits = 1) {
  if (value == null) return "—";
  const n = Number(value) * 100;
  return Number.isFinite(n) ? `${n.toFixed(digits)}%` : "—";
}

export default function ProbabilityCards({ forecast, advisory }) {
  const cards = {};
  for (const item of advisory?.items ?? []) cards[item.state] = item;

  return (
    <section className="panel">
      <h2>Target-state probabilities</h2>
      <div className="cards-grid">
        {forecast &&
          Object.keys(LABEL).map((t) => {
            const tg = forecast.targets?.[t] ?? {};
            const item = cards[t] ?? {};
            const raw = tg.probability;
            const band = tg.band ?? item.band ?? "low";
            const meaning = tg.band_meaning ?? item.band_meaning ?? "Possible";
            const color = BAND_COLOR[band] ?? "#334155";
            const interpretation = item.interpretation ?? SHORT[t];
            return (
              <article className="prob-card" key={t} data-testid={`card-${t}`}>
                <header
                  className="prob-card-head"
                  style={{ borderTopColor: color }}
                >
                  <h3>{LABEL[t]}</h3>
                  <span className="prob-value">{pct(raw)}</span>
                </header>
                <p className="prob-band" style={{ color }}>
                  {meaning} · {band.replace("_", " ")}
                </p>
                <p className="prob-interp">{interpretation}</p>
              </article>
            );
          })}
      </div>
      <p className="hint">
        Probability is a calibrated model output, not accuracy and not certainty.
      </p>
    </section>
  );
}