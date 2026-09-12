const ROWS = [
  { key: "rain_t_mm", label: "Rain today", unit: "mm" },
  { key: "sum7_mm", label: "7-day sum", unit: "mm" },
  { key: "rainfall_trend", label: "Rainfall trend", unit: "" },
  { key: "rainfall_regime", label: "Regime", unit: "" },
  { key: "wet_days_last7", label: "Wet days, last 7", unit: "days" },
  { key: "dry_streak_days", label: "Dry streak", unit: "days" },
  { key: "wet_streak_days", label: "Wet streak", unit: "days" },
];

export default function CurrentSignal({ advisory }) {
  const signal = advisory?.current_signal;
  if (!signal) return null;
  return (
    <section className="panel">
      <h2>Current signal</h2>
      <p className="lede">Observed inputs used by the frozen models.</p>
      <div className="signal-grid">
        {ROWS.map(({ key, label, unit }) => (
          <div className="signal-chip" key={key} data-testid={`signal-${key}`}>
            <span className="signal-label">{label}</span>
            <span className="signal-value">
              {signal[key] ?? "—"}
              {unit ? ` ${unit}` : ""}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}