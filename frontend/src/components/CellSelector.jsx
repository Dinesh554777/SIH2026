import { useMemo, useState } from "react";

const REGION_LABEL = {
  TN: "Tamil Nadu",
  MH: "Maharashtra",
  KA: "Karnataka",
};

export default function CellSelector({
  cells,
  selCell,
  cellInfo,
  date,
  onSelectCell,
  onDateChange,
}) {
  const [filter, setFilter] = useState("");

  const groups = useMemo(() => {
    const byRegion = {};
    for (const c of cells) {
      (byRegion[c.region] ||= []).push(c);
    }
    let list = Object.entries(byRegion)
      .map(([region, items]) => ({ region, items: [...items].sort((a, b) => a.cell_id.localeCompare(b.cell_id)) }))
      .sort((a, b) => a.region.localeCompare(b.region));
    if (filter.trim()) {
      const q = filter.trim().toLowerCase();
      list = list
        .map((g) => ({
          ...g,
          items: g.items.filter(
            (c) => c.cell_id.toLowerCase().includes(q) || String(c.lat).includes(q) || String(c.lon).includes(q)
          ),
        }))
        .filter((g) => g.items.length > 0);
    }
    return list;
  }, [cells, filter]);

  return (
    <section className="panel selector">
      <div className="selector-main">
        <h2>Pilot grid cell</h2>
        <div className="row-gap">
          <input
            type="search"
            className="filter-input"
            placeholder="Search cell ID / lat / lon…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            aria-label="Search pilot grid cells"
          />
          <select
            value={selCell}
            onChange={(e) => onSelectCell(e.target.value)}
            aria-label="Pilot grid cell"
            data-testid="cell-select"
          >
            {groups.length === 0 && <option value="">No matching cells</option>}
            {groups.map((g) => (
              <optgroup key={g.region} label={REGION_LABEL[g.region] ?? g.region}>
                {g.items.map((c) => (
                  <option key={c.cell_id} value={c.cell_id}>
                    {c.cell_id} · {REGION_LABEL[c.region] ?? c.region}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
          <label className="date-field">
            <span>Date</span>
            <input
              type="date"
              value={date}
              max="2024-12-31"
              onChange={(e) => onDateChange(e.target.value)}
              aria-label="Observation date"
            />
          </label>
        </div>
      </div>
      {cellInfo && (
        <div className="cell-meta" data-testid="cell-meta">
          <span className="cell-id">{cellInfo.cell_id}</span>
          <span>lat {cellInfo.lat}</span>
          <span>lon {cellInfo.lon}</span>
          <span>{REGION_LABEL[cellInfo.region] ?? cellInfo.region}</span>
          <span className="muted">{cellInfo.admin_note === "grid_cell_only" ? "grid cell — not a village/block" : ""}</span>
        </div>
      )}
    </section>
  );
}