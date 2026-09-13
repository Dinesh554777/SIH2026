import { useMemo, useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap, GeoJSON } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { REGION_LABEL } from "./labels";

// Fix leaflet default icon issue in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

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

// Map Controller to adjust view on selection
function MapController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, zoom, { duration: 1 });
    }
  }, [center, zoom, map]);
  return null;
}

export default function MapExplorer({
  geography,
  cells,
  selCell,
  cellInfo,
  date,
  village,
  riskIndex,
  onSelectCell,
  onSelectVillage,
  onDateChange,
}) {
  const [recent, pushRecent] = useRecent();
  const [query, setQuery] = useState("");
  const [path, setPath] = useState([]); // [{type,name}]
  const [mapCenter, setMapCenter] = useState([20.0, 77.0]);
  const [mapZoom, setMapZoom] = useState(5);

  const riskById = useMemo(() => {
    const m = new Map();
    (riskIndex?.cells ?? []).forEach((c) => m.set(c.cell_id, c));
    return m;
  }, [riskIndex]);

  const riskCounts = useMemo(() => {
    const counts = { low: 0, moderate: 0, high: 0, critical: 0 };
    riskById.forEach((c) => {
      if (c.risk_level in counts) counts[c.risk_level] += 1;
    });
    return counts;
  }, [riskById]);

  const villagesForCell = useMemo(() => {
    const m = new Map();
    if (geography?.hierarchy) {
      for (const st of geography.hierarchy)
        for (const d of st.districts)
          for (const b of d.blocks)
            for (const v of b.villages) {
              const list = m.get(v.cell_id) || [];
              list.push(`${v.name} · ${b.block.name}`);
              m.set(v.cell_id, list);
            }
    }
    return m;
  }, [geography]);

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
              (cell && REGION_LABEL[cell.region]?.toLowerCase().includes(q))
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
    if (cell) {
      setMapCenter([cell.lat, cell.lon]);
      setMapZoom(12);
    }
  };

  const pickRecent = (item) => {
    if (item.type === "village" && geography) {
      for (const st of geography.hierarchy)
        for (const d of st.districts)
          for (const b of d.blocks)
            for (const v of b.villages)
              if (v.village_id === item.village_id) {
                const cell = cells.find(c => c.cell_id === v.cell_id);
                pickVillage(v, cell);
                return;
              }
      return;
    }
    const cell = cells.find(c => c.cell_id === item.cell_id);
    onSelectCell(item.cell_id);
    if (cell) {
      setMapCenter([cell.lat, cell.lon]);
      setMapZoom(10);
    }
    setQuery("");
  };

  useEffect(() => {
    if (cellInfo) {
      setMapCenter([cellInfo.lat, cellInfo.lon]);
      // Only zoom in if we are not already zoomed in sufficiently
      if (mapZoom < 10) setMapZoom(10);
    }
  }, [cellInfo]);

  // Find hierarchy path for current village
  const currentHierarchy = useMemo(() => {
    if (!village || !geography) return null;
    for (const st of geography.hierarchy) {
      for (const d of st.districts) {
        for (const b of d.blocks) {
          for (const v of b.villages) {
            if (v.village_id === village.village_id) {
              return { state: st.state, district: d.district, block: b.block, village: v };
            }
          }
        }
      }
    }
    return null;
  }, [village, geography]);

  return (
    <section id="dashboard" className="panel location-panel">
      <div className="kicker">1 · Location Explorer</div>
      <h2>Select an Agricultural Region</h2>
      
      <div className="location-explorer-layout">
        <div className="explorer-controls">
          <div className="hierarchy-breadcrumb" data-testid="hierarchy-breadcrumb">
            {currentHierarchy ? (
              <>
                <span className="crumb">{currentHierarchy.state.name}</span>
                <span className="crumb">{currentHierarchy.district.name}</span>
                <span className="crumb">{currentHierarchy.block.name}</span>
                <span className="crumb" style={{ fontWeight: 'bold' }}>{currentHierarchy.village.name}</span>
              </>
            ) : (
              <span className="crumb">No village selected</span>
            )}
          </div>

          <div className="search-container">
            <input
              className="location-search"
              type="search"
              placeholder="Search village, block or district"
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
                        {m.block.name} · {m.district.name}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
            
            {recent.length > 0 && !query && (
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

        <div className="map-container-wrapper">
          <MapContainer center={mapCenter} zoom={mapZoom} style={{ height: "400px", width: "100%", borderRadius: "8px", border: "1px solid var(--border)" }}>
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapController center={mapCenter} zoom={mapZoom} />
            
            {cells.map((c) => {
              const isSelected = c.cell_id === selCell;
              // For demo, we are placing markers for all pilot cells
              return (
                <Marker 
                  key={c.cell_id} 
                  position={[c.lat, c.lon]}
                  eventHandlers={{
                    click: () => {
                      onSelectCell(c.cell_id);
                      setMapCenter([c.lat, c.lon]);
                      setMapZoom(11);
                    },
                  }}
                  opacity={isSelected ? 1 : 0.6}
                  zIndexOffset={isSelected ? 1000 : 0}
                >
                  <Popup>
                    <strong>Pilot Cell: {c.cell_id}</strong><br/>
                    Region: {REGION_LABEL[c.region] || c.region}
                    {isSelected && " (Selected)"}
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>
        </div>

        {village && currentHierarchy && (
          <div className="selected-location-card">
            <div className="sl-header">SELECTED LOCATION</div>
            <h3 className="sl-title">🌾 {village.name}</h3>
            <div className="sl-details">
              <div><strong>Block:</strong><br/>{currentHierarchy.block.name}</div>
              <div><strong>District:</strong><br/>{currentHierarchy.district.name}</div>
              <div><strong>State:</strong><br/>{currentHierarchy.state.name}</div>
              {cellInfo && (
                <div><strong>Coordinates:</strong><br/>{cellInfo.lat.toFixed(4)}, {cellInfo.lon.toFixed(4)}</div>
              )}
            </div>
            
            <div className="sl-actions">
               {/* Note: In App.jsx, the forecast loads automatically based on selCell. This button serves as a visual anchor. */}
               <button className="primary-button" onClick={() => document.getElementById("forecast-section")?.scrollIntoView({behavior: "smooth"})}>
                 View Forecast →
               </button>
            </div>
          </div>
        )}
      </div>

      <div className="advanced">
        <details>
          <summary>Advanced Settings</summary>
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
