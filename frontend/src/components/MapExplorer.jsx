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
  forecast,
  decision,
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
      
      <MapContainer center={mapCenter} zoom={mapZoom} style={{ flex: 1, width: "100%", zIndex: 0 }} zoomControl={false}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        <MapController center={mapCenter} zoom={mapZoom} />
        
        {cells.map((c) => {
          const isSelected = c.cell_id === selCell;
          const risk = riskById.get(c.cell_id);
          
          let color = 'var(--status-onset)'; // default green
          if (risk?.risk_level === 'critical') color = 'var(--status-low)'; // red
          else if (risk?.risk_level === 'high') color = 'var(--status-uncertain)'; // orange
          else if (risk?.risk_level === 'moderate') color = 'var(--status-likely)'; // yellow

          // Special styling for the selected cell
          const iconHtml = isSelected ? `
            <div style="
              width: 24px; 
              height: 24px; 
              background: ${color}; 
              border: 3px solid white; 
              border-radius: 50%;
              box-shadow: 0 0 0 4px rgba(0,0,0,0.1), 0 4px 10px rgba(0,0,0,0.3);
              display: flex;
              align-items: center;
              justify-content: center;
            "><div style="width: 8px; height: 8px; background: white; border-radius: 50%;"></div></div>
          ` : `
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
            iconSize: isSelected ? [24, 24] : [18, 18],
            iconAnchor: isSelected ? [12, 12] : [9, 9],
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
                {isSelected ? (
                  <div style={{ padding: '8px', minWidth: '220px', fontFamily: 'inherit' }}>
                    <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      {currentHierarchy ? `${getName(currentHierarchy.district)} / ${getName(currentHierarchy.block)}` : REGION_LABEL[c.region] || c.region}
                    </div>
                    <div style={{ fontSize: '16px', fontWeight: 'bold', color: '#0f172a', marginBottom: '12px' }}>
                      {forecast?.prediction?.status || 'UNKNOWN STATUS'}
                    </div>
                    
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span style={{ color: '#64748b' }}>Onset Prob:</span>
                      <strong style={{ color: '#0f172a' }}>{Math.round((forecast?.prediction?.onset_probability || 0) * 100)}%</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span style={{ color: '#64748b' }}>Rainfall:</span>
                      <strong style={{ color: '#0f172a' }}>{forecast?.recent_features?.recent_rainfall_mm?.toFixed(1) || 'N/A'} mm</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                      <span style={{ color: '#64748b' }}>Dry Spell Risk:</span>
                      <strong style={{ color: '#0f172a' }}>{Math.round((forecast?.risk_summary?.dry_spell_prob || 0) * 100)}%</strong>
                    </div>
                    
                    <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #e2e8f0' }}>
                      <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px' }}>Action:</div>
                      <strong style={{ fontSize: '14px', color: '#0f766e' }}>
                        {decision?.action || decision?.code || 'MONITOR'}
                      </strong>
                    </div>
                  </div>
                ) : (
                  <div style={{ padding: 4 }}>
                    <strong style={{ fontSize: '1.1em', display: 'block', marginBottom: 4 }}>
                      {REGION_LABEL[c.region] || c.region}
                    </strong>
                    {risk && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 8 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>Risk:</span>
                          <strong style={{ textTransform: 'capitalize', color }}>{risk.risk_level}</strong>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>Action:</span>
                          <strong>{risk.decision}</strong>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
