import React from 'react';
import { ComposedChart, Line, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useLanguage } from '../context/LanguageContext';
import { motion } from 'framer-motion';

export default function RainfallTrendChart({ forecast, historical }) {
  const { t } = useLanguage();
  
  const recentRain = forecast?.recent_features?.recent_rainfall_mm ?? null;
  const forecastRain = forecast?.forecast_features?.expected_rainfall_mm ?? null;

  // Ideally, `historical` would be an array of `{ date, actual, predicted }`
  let data = historical || [];
  
  if (data.length === 0) {
    if (recentRain !== null || forecastRain !== null) {
      // B. If real time-series data does not exist: display the available point values only.
      if (recentRain !== null) {
        data.push({ date: 'Recent', actual: recentRain, predicted: null });
      }
      if (forecastRain !== null) {
        data.push({ date: 'Forecast', actual: null, predicted: forecastRain });
      }
    } else {
      // C. If insufficient data exists: show unavailable.
      return (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass-panel" 
          style={{ padding: '20px', marginBottom: '16px', display: 'flex', flexDirection: 'column', minHeight: '280px' }}
        >
          <div style={{ fontSize: '13px', color: 'var(--muted)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '16px' }}>
            Rainfall Analytics (mm)
          </div>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontSize: '13px', textAlign: 'center' }}>
            Historical rainfall time-series unavailable for this location.
          </div>
        </motion.div>
      );
    }
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel" 
      style={{ padding: '20px', marginBottom: '16px' }}
    >
      <div style={{ fontSize: '13px', color: 'var(--muted)', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '16px' }}>
        Rainfall Analytics (mm)
      </div>
      
      <div style={{ height: '220px', width: '100%', marginLeft: '-20px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--muted)' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 11, fill: 'var(--muted)' }} axisLine={false} tickLine={false} />
            <Tooltip 
              cursor={{ fill: 'rgba(241, 245, 249, 0.5)' }} 
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: 'var(--shadow)', fontSize: '13px' }}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
            <Bar dataKey="actual" name="Observed" fill="var(--primary)" radius={[4, 4, 0, 0]} barSize={32} />
            <Bar dataKey="predicted" name="Forecast" fill="var(--status-likely)" radius={[4, 4, 0, 0]} barSize={32} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
