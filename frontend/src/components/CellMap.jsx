import { useMemo } from "react";
import { REGION_LABEL } from "./labels";

const REGION_COLOR = { TN: "#0f766e", MH: "#7c3aed", KA: "#b45309" };

export default function CellMap({ cells, selCell, onSelectCell }) {
  const geo = useMemo(() => {
    const byR = { TN: [], MH: [], KA: [] };
    for (const c of cells) (byR[c.region] ??= []).push(c);
    const g = {};
    for (const [r, list] of Object.entries(byR)) {
      const xs = list.map((c) => c.lon);
      const ys = list.map((c) => c.lat);
      g[r] = {
        minX: Math.min(...xs),
        maxX: Math.max(...xs),
        minY: Math.min(...ys),
        maxY: Math.max(...ys),
        items: list,
      };
    }
    return g;
  }, [cells]);

  const map = useMemo(() => {
    const allX = cells.map((c) => c.lon);
    const allY = cells.map((c) => c.lat);
    const minX = Math.min(...allX);
    const maxX = Math.max(...allX);
    const minY = Math.min(...allY);
    const maxY = Math.max(...allY);
    const pad = 0.4;
    const sx = (lon) => 20 + ((lon - minX) / (maxX - minX || 1)) * 460;
    const sy = (lat) => 20 + ((maxY - lat) / (maxY - minY || 1)) * 260;
    return { sx, sy, spanX: maxX - minX, spanY: maxY - minY };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cells]);

  return (
    <section className="panel map-panel" id="map">
      <div className="kicker">Grid overview</div>
      <h2>Pilot cells · {cells.length}</h2>
      <svg
        viewBox="0 0 500 300"
        role="img"
        aria-label="Map of pilot grid cells in Tamil Nadu, Maharashtra and Karnataka"
        data-testid="cell-map"
        className="cell-map-svg"
      >
        <rect width="500" height="300" className="map-bg" rx="10" />
        {cells.map((c) => {
          const [x, y] = [map.sx(c.lon), map.sy(c.lat)];
          const active = c.cell_id === selCell;
          return (
            <circle
              key={c.cell_id}
              cx={x}
              cy={y}
              r={active ? 6 : 3.5}
              fill={REGION_COLOR[c.region] ?? "#334155"}
              stroke={active ? "#fbbf24" : "none"}
              strokeWidth={active ? 2.5 : 0}
              className={active ? "map-dot map-dot-active" : "map-dot"}
              onClick={() => onSelectCell(c.cell_id)}
            >
              <title>{`${c.cell_id} · ${REGION_LABEL[c.region] ?? c.region}`}</title>
            </circle>
          );
        })}
        {Object.entries(geo).map(
          ([r, g]) =>
            g.items.length > 0 && (
              <text
                key={r}
                x={map.sx((g.minX + g.maxX) / 2)}
                y={map.sy((g.minY + g.maxY) / 2)}
                className="map-label"
              >
                {REGION_LABEL[r]}
              </text>
            )
        )}
        <circle cx="472" cy="16" r="4" fill="#fbbf24" />
        <text x="440" y="21" className="map-legend">
          selected
        </text>
      </svg>
      <p className="muted">
        Pilot grid cells (0.25°, ~25 × 25 km). Click a dot to switch the detail panel.
        A full boundary map is planned with authoritative GIS data.
      </p>
    </section>
  );
}