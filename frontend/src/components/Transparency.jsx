const LABEL = {
  onset: "Monsoon Onset",
  break: "Monsoon Break",
  revival: "Revival",
  dry_spell: "Dry Spell",
};

export default function Transparency({ modelInfo, forecast }) {
  const models = modelInfo?.models ?? {};
  const periods =
    modelInfo?.train_period || forecast?.provenance?.train_period;
  const dataMode =
    modelInfo?.data_mode ?? forecast?.data_mode ?? "historical/demo";

  const rows = Object.keys(LABEL).map((t) => {
    const m = models[t] ?? {};
    return {
      target: LABEL[t],
      model: m.selected_model ?? m.model ?? "—",
      featureGroup: m.feature_group ?? "—",
      extra: m.n_features ? `${m.n_features} features` : "",
    };
  });

  return (
    <section className="panel">
      <h2>Model transparency</h2>
      <table className="transparency-table">
        <thead>
          <tr>
            <th>Target</th>
            <th>Model</th>
            <th>Feature group</th>
            <th>Detail</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.target}>
              <td>{r.target}</td>
              <td>{r.model}</td>
              <td>{r.featureGroup}</td>
              <td>{r.extra}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <dl className="meta-grid">
        <div>
          <dt>Training period</dt>
          <dd>{periods ?? "—"}</dd>
        </div>
        <div>
          <dt>Validation period</dt>
          <dd>{modelInfo?.validation_period ?? forecast?.provenance?.validation_period ?? "—"}</dd>
        </div>
        <div>
          <dt>Test period</dt>
          <dd>{modelInfo?.test_period ?? forecast?.provenance?.test_period ?? "—"}</dd>
        </div>
        <div>
          <dt>Mode</dt>
          <dd data-testid="transparency-mode">{dataMode}</dd>
        </div>
        <div>
          <dt>Model version</dt>
          <dd>{modelInfo?.model_version ?? forecast?.provenance?.freeze_digest ?? "—"}</dd>
        </div>
        <div>
          <dt>Freeze digest</dt>
          <dd>
            <code>{modelInfo?.freeze_digest ?? forecast?.provenance?.freeze_digest ?? "—"}</code>
          </dd>
        </div>
      </dl>
      {modelInfo?.forecast_horizon_note && (
        <p className="muted">{modelInfo.forecast_horizon_note}</p>
      )}
    </section>
  );
}