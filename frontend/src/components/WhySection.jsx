function fmt(x, digits = 2) {
  if (x == null) return "—";
  const n = Number(x);
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

const FEATURE_LABEL = {
  imd_rain_t: "IMD rain (today)",
  imd_sum3: "IMD 3-day rain",
  imd_sum7: "IMD 7-day rain",
  imd_sum14: "IMD 14-day rain",
  imd_days_since_wet: "Days since wet day",
  imd_consec_dry: "Consecutive dry days",
  imd_anom_t: "Rain anomaly (today)",
  th_accel: "Thornton humidity accel.",
  th_cv7: "CV of 7-day rain",
  th_wet_streak: "Wet streak",
  th_dry_streak: "Dry streak",
  th_sum10: "10-day rain sum",
  th_wetcount7: "Wet-day count (7d)",
  chirps_rain: "CHIRPS rain",
};

export default function WhySection({ explainData }) {
  if (!explainData) {
    return (
      <section className="panel">
        <h2>Why this forecast?</h2>
        <p className="muted">No explanation available for this selection.</p>
      </section>
    );
  }
  const sens = explainData.sensitivity ?? [];
  return (
    <section className="panel">
      <h2>Why this forecast?</h2>
      <p className="caveat-strong" role="note" data-testid="sensitivity-caveat">
        Model sensitivity — not causal explanation
      </p>
      <p className="lede">
        One-at-a-time sensitivity of the {LABEL_TARGET(explainData.target)} model (
        {explainData.model}, group {explainData.feature_group}) — how the
        probability changes when each feature moves from its training median to
        the observed value.
      </p>
      <table className="why-table">
        <thead>
          <tr>
            <th>Feature</th>
            <th>Observed</th>
            <th>Train median</th>
            <th>Δ probability</th>
          </tr>
        </thead>
        <tbody>
          {sens.map((s) => {
            const delta = Number(s.delta_probability ?? 0) * 100;
            const w = Math.min(Math.abs(delta) / 60, 1) * 100;
            return (
              <tr key={s.feature}>
                <td className="feat">{FEATURE_LABEL[s.feature] ?? s.feature}</td>
                <td>{fmt(s.value)}</td>
                <td>{fmt(s.train_median)}</td>
                <td className="delta-cell">
                  <span className={delta >= 0 ? "delta-pos" : "delta-neg"}>
                    {delta >= 0 ? "+" : ""}
                    {delta.toFixed(2)} pts
                  </span>
                  <span className="delta-bar">
                    <span
                      className={
                        delta >= 0 ? "delta-fill-pos" : "delta-fill-neg"
                      }
                      style={{ width: `${w}%` }}
                    />
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="muted">{explainData.caveat}</p>
    </section>
  );
}

function LABEL_TARGET(t) {
  return { onset: "Onset", break: "Break", revival: "Revival", dry_spell: "Dry spell" }[t] ?? t;
}