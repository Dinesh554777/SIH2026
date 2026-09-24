import React, { useState, useEffect } from 'react';
import { MapPin, ChevronDown } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { motion } from 'framer-motion';

export default function LocationSelector({ geography, currentLoc, onSelectLocation }) {
  const [selState, setSelState] = useState('');
  const [selDist, setSelDist] = useState('');
  const [selBlock, setSelBlock] = useState('');
  const [selVill, setSelVill] = useState('');
  const { t } = useLanguage();

  // Sync initial state if provided
  useEffect(() => {
    if (currentLoc && currentLoc.village_id) {
      setSelState(currentLoc.state_id || currentLoc.state?.state_id || (typeof currentLoc.state === 'string' ? currentLoc.state : ''));
      setSelDist(currentLoc.district_id || currentLoc.district?.district_id || (typeof currentLoc.district === 'string' ? currentLoc.district : ''));
      setSelBlock(currentLoc.block_id || currentLoc.block?.block_id || (typeof currentLoc.block === 'string' ? currentLoc.block : ''));
      setSelVill(currentLoc.village_id || currentLoc.village?.village_id || '');
    }
  }, [currentLoc]);

  // Pre-select first options if geography is loaded and nothing is selected
  useEffect(() => {
    if (!selState && geography?.hierarchy?.length > 0) {
      const st = geography.hierarchy[0];
      setSelState(st.state_id || st.name);
      
      if (st.districts?.length > 0) {
        const d = st.districts[0];
        setSelDist(d.district_id || d.name);
        
        if (d.blocks?.length > 0) {
          const b = d.blocks[0];
          setSelBlock(b.block_id || b.name);
          
          if (b.villages?.length > 0) {
            const v = b.villages[0];
            setSelVill(v.village_id);
            handleSelect(st, d, b, v);
          }
        }
      }
    }
  }, [geography, selState]);

  const hierarchy = geography?.hierarchy || [];
  
  const currentStateObj = hierarchy.find(s => (s.state?.geography_id || s.state?.name) === selState) || hierarchy[0];
  const districts = currentStateObj?.districts || [];
  
  const currentDistObj = districts.find(d => (d.district?.geography_id || d.district?.name) === selDist) || districts[0];
  const blocks = currentDistObj?.blocks || [];
  
  const currentBlockObj = blocks.find(b => (b.block?.geography_id || b.block?.name) === selBlock) || blocks[0];
  const villages = currentBlockObj?.villages || [];

  const handleSelect = (st, d, b, v) => {
    if (!v) return;
    onSelectLocation({
      state: st.state,
      district: d.district,
      block: b.block,
      village: v,
      village_id: v.village_id,
      name: v.name || v.village_name,
      cell_id: v.cell_id,
      lat: v.lat,
      lon: v.lon
    });
  };

  const selectStyle = {
    width: '100%',
    padding: '10px 14px',
    borderRadius: '8px',
    border: '1px solid var(--line)',
    backgroundColor: 'var(--surface)',
    fontSize: '14px',
    color: 'var(--ink)',
    outline: 'none',
    cursor: 'pointer',
    appearance: 'none'
  };

  const selectWrapperStyle = {
    position: 'relative',
    marginBottom: '12px'
  };

  const selectIconStyle = {
    position: 'absolute',
    right: '12px',
    top: '50%',
    transform: 'translateY(-50%)',
    pointerEvents: 'none',
    color: 'var(--muted)'
  };

  if (!geography) {
    return (
      <div className="glass-panel" style={{ padding: '20px', color: 'var(--muted)', fontSize: '14px', textAlign: 'center' }}>
        Loading location data...
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="glass-panel" 
      style={{ padding: '20px', marginBottom: '16px' }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--primary)', fontWeight: '700', marginBottom: '16px', fontSize: '15px' }}>
        <MapPin size={20} />
        <span>Location Selection</span>
      </div>
      
      <div style={selectWrapperStyle}>
        <select 
          style={selectStyle}
          value={selState} 
          onChange={e => {
            setSelState(e.target.value);
            setSelDist(''); setSelBlock(''); setSelVill('');
          }}
        >
          <option value="" disabled>Select State</option>
          {hierarchy.map(s => <option key={s.state?.geography_id || s.state?.name} value={s.state?.geography_id || s.state?.name}>{s.state?.name}</option>)}
        </select>
        <ChevronDown size={16} style={selectIconStyle} />
      </div>

      <div style={selectWrapperStyle}>
        <select 
          style={{...selectStyle, opacity: !districts.length ? 0.5 : 1}}
          value={selDist} 
          onChange={e => {
            setSelDist(e.target.value);
            setSelBlock(''); setSelVill('');
          }}
          disabled={!districts.length}
        >
          <option value="" disabled>{!districts.length ? 'No districts available' : 'Select District'}</option>
          {districts.map(d => <option key={d.district?.geography_id || d.district?.name} value={d.district?.geography_id || d.district?.name}>{d.district?.name}</option>)}
        </select>
        <ChevronDown size={16} style={selectIconStyle} />
      </div>

      <div style={selectWrapperStyle}>
        <select 
          style={{...selectStyle, opacity: !blocks.length ? 0.5 : 1}}
          value={selBlock} 
          onChange={e => {
            setSelBlock(e.target.value);
            setSelVill('');
          }}
          disabled={!blocks.length}
        >
          <option value="" disabled>{!blocks.length ? 'No blocks available' : 'Select Block'}</option>
          {blocks.map(b => <option key={b.block?.geography_id || b.block?.name} value={b.block?.geography_id || b.block?.name}>{b.block?.name}</option>)}
        </select>
        <ChevronDown size={16} style={selectIconStyle} />
      </div>

      <div style={selectWrapperStyle}>
        <select 
          style={{...selectStyle, opacity: !villages.length ? 0.5 : 1, marginBottom: 0}}
          value={selVill} 
          onChange={e => {
            const vId = e.target.value;
            setSelVill(vId);
            const v = villages.find(x => x.village_id === vId);
            if (v) handleSelect(currentStateObj, currentDistObj, currentBlockObj, v);
          }}
          disabled={!villages.length}
        >
          <option value="" disabled>{!villages.length ? 'No villages available' : 'Select Village/Cell'}</option>
          {villages.map(v => <option key={v.village_id} value={v.village_id}>{v.name || v.village_name}</option>)}
        </select>
        <ChevronDown size={16} style={selectIconStyle} />
      </div>
    </motion.div>
  );
}
