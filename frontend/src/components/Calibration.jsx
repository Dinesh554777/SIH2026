import { useLanguage } from '../context/LanguageContext.jsx';

function asPct(v) {
  if (v == null) return "—";
  const n = Number(v) * 100;
  return Number.isFinite(n) ? `${n.toFixed(2)}%` : "—";
}

export default function Calibration({ forecast }) {
  const { t } = useLanguage();
  const calibration = forecast?.confidence?.calibration ?? [];

  const LABEL = {
    onset: t("risk.onset") ?? "Monsoon Onset",
    break: t("risk.break") ?? "Monsoon Break",
    revival: "Revival",
    dry_spell: t("risk.dry_spell") ?? "Dry Spell",
  };

  return (
    <section className="panel">
      <h2>{t("history.calibrationTitle") ?? "Algorithm calibration"}</h2>
      <blockquote className="calibration-quote">
        {t("history.calibrationNote") ?? "Probabilities represent estimated likelihood, not certainty."}
      </blockquote>
      <p className="lede">
        Validation-calibrated outputs: the expected calibration error (ECE) and Brier score on the 2022–2023 validation period. Lower is tighter.
      </p>
      {calibration.length > 0 ? (
        <table className="calibration-table">
          <thead>
            <tr>
              <th>Target</th>
              <th>ECE</th>
              <th>Brier</th>
              <th>Validation period</th>
            </tr>
          </thead>
          <tbody>
            {calibration.map((c) => (
              <tr key={c.state}>
                <td>{LABEL[c.state] ?? c.state}</td>
                <td>{asPct(c.ece)}</td>
                <td>{c.brier != null ? Number(c.brier).toFixed(4) : "—"}</td>
                <td>{c.period ?? "2022–2023"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="muted">No calibration metrics returned by the backend.</p>
      )}
    </section>
  );
}
