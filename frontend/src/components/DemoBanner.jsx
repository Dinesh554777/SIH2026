export default function DemoBanner({ visible = true }) {
  if (!visible) return null;
  return (
    <div className="demo-banner" role="note">
      <strong>HISTORICAL / DEMO MODE</strong>
      <span>
        — these are historical-model demonstrations on recorded monsoon
        observations, not live forecasts.
      </span>
    </div>
  );
}