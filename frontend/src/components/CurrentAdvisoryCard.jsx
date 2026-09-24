import React, { useState } from 'react';
import { Sprout, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { motion, AnimatePresence } from 'framer-motion';

export default function CurrentAdvisoryCard({ decision }) {
  const { t } = useLanguage();
  const [expanded, setExpanded] = useState(false);
  
  const actionCode = (decision?.code || decision?.action || "WAIT").toUpperCase();
  const explanation = decision?.reason || decision?.explanation || "Conditions are not yet completely stable for sowing. Monitor closely.";
  
  const actionConfig = {
    SOW: { bg: 'var(--primary)', color: 'white', icon: Sprout },
    WAIT: { bg: 'var(--status-likely)', color: '#fff', icon: Clock },
    IRRIGATE: { bg: 'var(--accent)', color: 'white', icon: Sprout },
    MONITOR: { bg: 'var(--status-uncertain)', color: 'white', icon: Clock }
  };
  
  const config = actionConfig[actionCode] || actionConfig.WAIT;
  const Icon = config.icon;

  const factors = decision?.factors || [
    { label: "Rainfall consistency", value: "Insufficient", ok: false },
    { label: "Forecast stability", value: "Moderate", ok: true },
    { label: "Dry-spell risk", value: "Elevated", ok: false }
  ];
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="glass-panel" 
      style={{ padding: '20px', marginBottom: '16px', borderLeft: `4px solid ${config.bg}` }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--muted)', fontWeight: '600', fontSize: '13px', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
        <span>Agricultural Action</span>
      </div>
      
      <div style={{ 
        display: 'inline-flex', 
        alignItems: 'center', 
        gap: '8px', 
        backgroundColor: config.bg, 
        color: config.color,
        padding: '8px 16px',
        borderRadius: '8px',
        fontWeight: '800',
        fontSize: '20px',
        marginBottom: '16px',
        boxShadow: 'var(--shadow)'
      }}>
        <Icon size={22} />
        {actionCode.replace(/_/g, ' ')}
      </div>
      
      <p style={{ fontSize: '14px', color: 'var(--ink)', margin: '0 0 16px 0', lineHeight: '1.5', fontWeight: '500' }}>
        {explanation}
      </p>

      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--line)', paddingTop: '12px' }}>
        <div style={{ fontSize: '12px', color: 'var(--muted)', fontWeight: '500' }}>
          Next review: <span style={{ color: 'var(--ink)', fontWeight: '600' }}>Tomorrow</span>
        </div>
        
        <button 
          onClick={() => setExpanded(!expanded)}
          style={{ background: 'transparent', border: 'none', color: 'var(--primary)', fontSize: '13px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px', cursor: 'pointer' }}
        >
          Why {actionCode}?
          {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{ backgroundColor: 'var(--bg)', borderRadius: '8px', padding: '12px', marginTop: '12px' }}>
              <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {factors.map((f, i) => (
                  <li key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span style={{ color: 'var(--muted)' }}>{f.label}</span>
                    <span style={{ fontWeight: '600', color: f.ok ? 'var(--status-onset)' : 'var(--status-low)' }}>
                      {f.ok ? '✓ ' : '⚠ '}{f.value}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
