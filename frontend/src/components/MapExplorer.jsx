import { useMemo, useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { REGION_LABEL } from "./labels";
import { Search } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext.jsx';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

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
    } catch {}
  };
  return [recent, push];
}

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
  village,
  riskIndex,
  onSelectCell,
  onSelectVillage,
}) {
  const { t, lang } = useLanguage();
  const [recent, pushRecent] = useRecent();
  const [query, setQuery] = useState("");
  const [mapCenter, setMapCenter] = useState([20.0, 77.0]);
  const [mapZoom, setMapZoom] = useState(6);

  const getName = (obj) => {
    if (!obj) return "";
    if (lang === 'ta') {
      return obj.name_ta || obj.state_name_ta || obj.district_name_ta || obj.block_name_ta || obj.village_name_ta || obj.name || "";
    }
    return obj.name_en || obj.state_name_en || obj.district_name_en || obj.block_name_en || obj.village_name_en || obj.name || "";
  };

  const riskById = useMemo(() => {
    const m = new Map();
    (riskIndex?.cells ?? []).forEach((c) => m.set(c.cell_id, c));
    return m;
  }, [riskIndex]);

  const riskCounts = useMemo(() => {
    const counts = { low: 0, moderate: 0, high: 0, critical: 0 };
    (riskIndex?.cells ?? []).forEach((c) => {
      if (counts[c.risk_level] !== undefined) counts[c.risk_level] += 1;
    });
    return counts;
  }, [riskIndex]);

  const villagesForCell = useMemo(() => {
    const m = new Map();
    if (geography?.hierarchy) {
      for (const st of geography.hierarchy)
        for (const d of st.districts)
          for (const b of d.blocks)
            for (const v of b.villages) {
              const list = m.get(v.cell_id) || [];
              list.push(`${getName(v)} · ${getName(b.block)}`);
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
              getName(v).toLowerCase().includes(q) ||
              v.cell_id.toLowerCase().includes(q) ||
              getName(b.block).toLowerCase().includes(q) ||
              getName(d.district).toLowerCase().includes(q) ||
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
      label: `${getName(villageObj)} · ${villageObj.village_id}`,
      cell_id: villageObj.cell_id,
      village_id: villageObj.village_id,
    });
    if (cell) {
      setMapCenter([cell.lat, cell.lon]);
      setMapZoom(12);
    }
  };

  useEffect(() => {
    if (cellInfo) {
      setMapCenter([cellInfo.lat, cellInfo.lon]);
      if (mapZoom < 10) setMapZoom(10);
    }
  }, [cellInfo]);

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
    <div className="map-explorer-container" style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
      {/* Location Search Overlay and Risk Legend moved to sidebar/redesign */}

      <MapContainer center={mapCenter} zoom={mapZoom} style={{ flex: 1, width: "100%", zIndex: 0 }} zoomControl={false}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />
        <MapController center={mapCenter} zoom={mapZoom} />
        
        {cells.map((c) => {
          const isSelected = c.cell_id === selCell;
          const risk = riskById.get(c.cell_id);
          
          let color = '#3b82f6'; // default
          if (risk?.risk_level === 'critical') color = '#ef4444';
          else if (risk?.risk_level === 'high') color = '#f97316';
          else if (risk?.risk_level === 'moderate') color = '#eab308';
          else if (risk?.risk_level === 'low') color = '#10b981';

          const iconHtml = `
            <div style="
              width: 14px; 
              height: 14px; 
              background: ${color}; 
              border: 2px solid white; 
              border-radius: 50%;
              box-shadow: 0 1px 4px rgba(0,0,0,0.3);
            "></div>
          `;

          const customIcon = L.divIcon({
            html: iconHtml,
            className: '',
            iconSize: [18, 18],
            iconAnchor: [9, 9],
          });

          return (
            <Marker
              key={c.cell_id}
              position={[c.lat, c.lon]}
              icon={customIcon}
              eventHandlers={{
                click: () => {
                  onSelectCell(c.cell_id);
                  setMapCenter([c.lat, c.lon]);
                  setMapZoom(11);
                },
              }}
              zIndexOffset={isSelected ? 1000 : 0}
            >
              <Popup>
                <div style={{ padding: 4 }}>
                  <strong style={{ fontSize: '1.1em', display: 'block', marginBottom: 4 }}>
                    {REGION_LABEL[c.region] || c.region}
                  </strong>
                  {risk && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Risk:</span>
                        <strong style={{ textTransform: 'capitalize', color }}>{t(`risk.${risk.risk_level === 'moderate' ? 'medium' : risk.risk_level}`) || risk.risk_level}</strong>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Action:</span>
                        <strong>{t(`decisions.${risk.decision}`) || risk.decision}</strong>
                      </div>
                    </div>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      {/* Floating Selected Location Card */}
      {village && currentHierarchy && (
        <div style={{ position: 'absolute', bottom: 24, left: '50%', transform: 'translateX(-50%)', zIndex: 1000, background: '#fff', borderRadius: 12, padding: 16, boxShadow: '0 8px 24px rgba(0,0,0,0.15)', minWidth: 280, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 700, color: '#64748b', letterSpacing: 1 }}>SELECTED LOCATION</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#1e293b' }}>📍 {getName(village)}</div>
          <div style={{ display: 'flex', gap: 16, fontSize: '0.85rem', color: '#475569', marginTop: 4 }}>
            <div>
              <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: '#94a3b8' }}>Block</div>
              <div style={{ fontWeight: 600 }}>{getName(currentHierarchy.block)}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.7rem', textTransform: 'uppercase', color: '#94a3b8' }}>District</div>
              <div style={{ fontWeight: 600 }}>{getName(currentHierarchy.district)}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
