import React from 'react';
import { useLanguage } from '../context/LanguageContext';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { motion } from 'framer-motion';

export default function WhatChanged({ previous, current }) {
  const { t } = useLanguage();

  if (!previous || !current) return null;

  const getChangeIcon = (prev, curr, invertGood = false) => {
    if (curr > prev) return <TrendingUp size={14} color={invertGood ? 'var(--status-low)' : 'var(--status-onset)'} />;
    if (curr < prev) return <TrendingDown size={14} color={invertGood ? 'var(--status-onset)' : 'var(--status-low)'} />;
    return <Minus size={14} color="var(--muted)" />;
  };

  const prevOnset = previous.prediction?.onset_probability || 0;
  const currOnset = current.prediction?.onset_probability || 0;
  
  const prevRain = previous.forecast_features?.expected_rainfall_mm || 0;
  const currRain = current.forecast_features?.expected_rainfall_mm || 0;

  const prevRisk = previous.risk_summary?.dry_spell_prob || 0;
  const currRisk = current.risk_summary?.dry_spell_prob || 0;

  const prevStatus = previous.prediction?.status || 'UNCERTAIN';
  const currStatus = current.prediction?.status || 'UNCERTAIN';

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel" style={{ padding: '20px', marginBottom: '16px' }}
    >
      <div style={{ fontSize: '13px', color: 'var(--muted)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '16px' }}>
        What Changed?
      </div>

      <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--line)', color: 'var(--muted)', textAlign: 'left' }}>
            <th style={{ paddingBottom: '8px', fontWeight: '500' }}>Metric</th>
            <th style={{ paddingBottom: '8px', fontWeight: '500' }}>Previous</th>
            <th style={{ paddingBottom: '8px', fontWeight: '500' }}>Current</th>
            <th style={{ paddingBottom: '8px', fontWeight: '500' }}>Trend</th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ borderBottom: '1px solid var(--line)' }}>
            <td style={{ padding: '12px 0', fontWeight: '600', color: 'var(--ink)' }}>Status</td>
            <td style={{ padding: '12px 0', color: 'var(--muted)' }}>{prevStatus}</td>
            <td style={{ padding: '12px 0', fontWeight: '700', color: prevStatus !== currStatus ? 'var(--primary)' : 'var(--ink)' }}>{currStatus}</td>
            <td style={{ padding: '12px 0', fontSize: '11px', color: 'var(--muted)' }}>{prevStatus !== currStatus ? 'Changed' : 'No change'}</td>
          </tr>
          <tr style={{ borderBottom: '1px solid var(--line)' }}>
            <td style={{ padding: '12px 0', fontWeight: '600', color: 'var(--ink)' }}>Probability</td>
            <td style={{ padding: '12px 0', color: 'var(--muted)' }}>{Math.round(prevOnset * 100)}%</td>
            <td style={{ padding: '12px 0', fontWeight: '700', color: 'var(--ink)' }}>{Math.round(currOnset * 100)}%</td>
            <td style={{ padding: '12px 0', fontSize: '11px', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              {getChangeIcon(prevOnset, currOnset)} 
              {Math.abs(Math.round((currOnset - prevOnset) * 100))} percentage points
            </td>
          </tr>
          <tr style={{ borderBottom: '1px solid var(--line)' }}>
            <td style={{ padding: '12px 0', fontWeight: '600', color: 'var(--ink)' }}>Rainfall</td>
            <td style={{ padding: '12px 0', color: 'var(--muted)' }}>{Math.round(prevRain)} mm</td>
            <td style={{ padding: '12px 0', fontWeight: '700', color: 'var(--ink)' }}>{Math.round(currRain)} mm</td>
            <td style={{ padding: '12px 0', fontSize: '11px', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              {getChangeIcon(prevRain, currRain)}
              {Math.abs(Math.round(currRain - prevRain))} mm difference
            </td>
          </tr>
          <tr>
            <td style={{ padding: '12px 0', fontWeight: '600', color: 'var(--ink)' }}>Dry-spell risk</td>
            <td style={{ padding: '12px 0', color: 'var(--muted)' }}>{Math.round(prevRisk * 100)}%</td>
            <td style={{ padding: '12px 0', fontWeight: '700', color: 'var(--ink)' }}>{Math.round(currRisk * 100)}%</td>
            <td style={{ padding: '12px 0', fontSize: '11px', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              {getChangeIcon(prevRisk, currRisk, true)}
              {Math.abs(Math.round((currRisk - prevRisk) * 100))} percentage points
            </td>
          </tr>

        </tbody>
      </table>
    </motion.div>
  );
}
