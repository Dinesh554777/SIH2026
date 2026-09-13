import { useMemo, useState } from "react";
import { REGION_LABEL } from "./labels";

const today = new Date().toISOString().slice(0, 10);

function useRecent() {
  const [recent, setRecent] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("sih.recentLocations") || "[]");
    } catch {
      return [];
    }
  });
  const push = (item) => {
    if (!item?.cell_id) return;
    const next = [item, ...recent.filter((r) => r.cell_id !== item.cell_id)].slice(0, 4);
    setRecent(next);
    try {
      localStorage.setItem("sih.recentLocations", JSON.stringify(next));
    } catch {
      /* private mode */
    }
  };
  return [recent, push];
}

export default function LocationSelector({
  geography,
  cells,
  selCell,
  cellInfo,
  date,
  village,
  onSelectCell,
  onSelectVillage,
  onDateChange,
}) {
  const [recent, pushRecent] = useRecent();
  const [query, setQuery] = useState("");
  const [path, setPath] = useState([]); // [{type,name}]

  const matches = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.trim().toLowerCase();
    const out = [];
    if (!geography?.hierarchy) return out;
    for (const st of geography.hierarchy) {
      for (const d of st.districts) {
        for (const b of d.blocks) {
          for (const v of b.villages) {
            const cell = cells.find((c) => c.cell_id === v.cell_id);
            if (
              v.name.toLowerCase().includes(q) ||
              v.cell_id.toLowerCase().includes(q) ||
              b.block.name.toLowerCase().includes(q) ||
              d.district.name.toLowerCase().includes(q) ||
              geometry_region_match(cell, q)
            ) {
              out.push({
                village: v,
                state: st.state,
                district: d.district,
                block: b.block,
                cell: cell,
                region: cell?.region,
              });
            }
          }
        }
      }
    }
    return out.slice(0, 8);
  }, [query, geography, cells]);

  const pickVillage = (villageObj, cell) => {
    onSelectVillage(villageObj, villageObj.cell_id);
    setQuery("");
    pushRecent({
      type: "village",
      label: `${villageObj.name} · ${villageObj.village_id}`,
      cell_id: villageObj.cell_id,
      village_id: villageObj.village_id,
    });
  };

  const pickRecent = (item) => {
    if (item.type === "village" && geography) {
      for (const st of geography.hierarchy)
        for (const d of st.districts)
          for (const b of d.blocks)
            for (const v of b.villages)
              if (v.village_id === item.village_id) {
                onSelectVillage(v, v.cell_id);
                setQuery("");
                return;
              }
      return;
    }
    onSelectCell(item.cell_id);
    setQuery("");
  };

  return (
    <section id="dashboard" className="panel location-panel">
      <div className="kicker">1 · Location</div>
      <h2>Pick a village or grid cell</h2>
      <p className="location-note">{geography?.note ?? ""}</p>

      {geography && (
        <>
          <div className="hierarchy-breadcrumb" data-testid="hierarchy-breadcrumb">
            {path.length === 0 && (
              <span className="crumb">
                States · {geography.hierarchy.length}
              </span>
            )}
            {path.map((p, i) => (
              <span key={i} className="crumb">
                {p.name}
              </span>
            ))}
          </div>

          <div className="browse-row">
            <div className="browse-level" data-testid="state-list">
              {path.length === 0 &&
                geography.hierarchy.map((st) => (
                  <button
                    key={st.state.geography_id}
                    className="browse-item"
                    onClick={() => setPath([{ type: "state", name: st.state.name, node: st }])}
                  >
                    <span className="browse-main">{st.state.name}</span>
                    <span className="browse-chev">›</span>
                  </button>
                ))}
              {path.at(-1)?.type === "state" &&
                path.at(-1).node.districts.map((d) => (
                  <button
                    key={d.district.geography_id}
                    className="browse-item"
                    onClick={() =>
                      setPath([
                        ...path,
                        { type: "district", name: d.district.name, node: d },
                      ])
                    }
                  >
                    <span className="browse-main">{d.district.name}</span>
                    <span className="browse-sub">{d.blocks.length} blocks</span>
                    <span className="browse-chev">›</span>
                  </button>
                ))}
              {path.at(-1)?.type === "district" &&
                path.at(-1).node.blocks.map((b) => (
                  <button
                    key={b.block.geography_id}
                    className="browse-item"
                    onClick={() =>
                      setPath([
                        ...path,
                        { type: "block", name: b.block.name, node: b, district: path.at(-1) },
                      ])
                    }
                  >
                    <span className="browse-main">{b.block.name}</span>
                    <span className="browse-sub">
                      {b.villages.length} villages · pilot {b.pilot_cell}
                    </span>
                    <span className="browse-chev">›</span>
                  </button>
                ))}
              {path.at(-1)?.type === "block" &&
                path.at(-1).node.villages.map((v) => {
                  const cell = cells.find((c) => c.cell_id === v.cell_id);
                  const active = selCell === v.cell_id;
                  return (
                    <button
                      key={v.village_id}
                      className={`browse-item ${active ? "browse-item-active" : ""}`}
                      data-testid="village-item"
                      onClick={() => {
                        onSelectVillage(v, v.cell_id);
                        pushRecent({
                          type: "village",
                          label: `${v.name} · ${v.village_id}`,
                          cell_id: v.cell_id,
                          village_id: v.village_id,
                        });
                      }}
                    >
                      <span className="browse-main">{v.name}</span>
                      <span className="browse-sub">
                        grid {v.cell_id.replace("_", ", ")} ·{" "}
                        {cell ? REGION_LABEL[cell.region] : "pilot grid"}
                      </span>
                    </button>
                  );
                })}
            </div>

            <div className="browse-side">
              <input
                className="location-search"
                type="search"
                placeholder="Search village, block or grid (e.g. Orathanadu, 10.75_77.5)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Search demo locations"
              />
              {query && (
                <ul className="autocomplete" data-testid="autocomplete">
                  {matches.length === 0 && <li className="autocomplete-empty">No matches</li>}
                  {matches.map((m) => (
                    <li key={m.village.village_id}>
                      <button onClick={() => pickVillage(m.village, m.cell)}>
                        <span className="ac-main">{m.village.name}</span>
                        <span className="ac-sub">
                          {m.block.block.name} · {m.district.district.name} · grid{" "}
                          {m.village.cell_id.replace("_", ", ")}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {recent.length > 0 && (
                <div className="recent" data-testid="recent-locations">
                  <span className="recent-label">Recent</span>
                  {recent.map((r) => (
                    <button key={r.cell_id} className="recent-chip" onClick={() => pickRecent(r)}>
                      {r.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}

      <div className="advanced">
        <details open={!geography}>
          <summary>
            Advanced: choose a pilot grid cell directly {geography ? "(fine control)" : ""}
          </summary>
          <div className="advanced-row">
            <select
              className="cell-select"
              data-testid="cell-select"
              value={selCell}
              onChange={(e) => onSelectCell(e.target.value)}
            >
              {cells.map((c) => (
                <option key={c.cell_id} value={c.cell_id}>
                  {c.cell_id.replace("_", ", ")} — {REGION_LABEL[c.region] || c.region}
                </option>
              ))}
            </select>
            <select
              className="date-field"
              data-testid="date-field"
              value={date}
              onChange={(e) => onDateChange(e.target.value)}
              aria-label="Forecast date"
            >
              <option value={today}>Latest scenario date</option>
              <option value="2024-08-12">2024-08-12</option>
              <option value="2024-06-07">2024-06-07</option>
              <option value="2024-08-08">2024-08-08</option>
              <option value="2024-08-11">2024-08-11</option>
              <option value="2024-09-29">2024-09-29</option>
            </select>
          </div>
          <div className="cell-meta" data-testid="cell-meta">
            Selected cell <strong>{selCell}</strong>
            {cellInfo && (
              <>
                {" · "}
                <strong>{REGION_LABEL[cellInfo.region] || cellInfo.region}</strong>
                {" · nearest station "}
                {cellInfo.nearest_station_id ?? "–"}
              </>
            )}
            {village && (
              <>
                {" · village "}
                <strong data-testid="village-name">{village.name}</strong>
              </>
            )}
          </div>
        </details>
      </div>
    </section>
  );
}

function geometry_region_match(cell, q) {
  if (!cell) return false;
  return REGION_LABEL[cell.region]?.toLowerCase().includes(q);
}