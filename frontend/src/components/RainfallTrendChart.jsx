import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useLanguage } from '../context/LanguageContext';

export default function RainfallTrendChart() {
  const { t } = useLanguage();
  const data = [
    { name: '12 Jun', rain: 20 },
    { name: '13 Jun', rain: 35 },
    { name: '14 Jun', rain: 50 },
    { name: '15 Jun', rain: 60 },
    { name: '16 Jun', rain: 90 },
    { name: '17 Jun', rain: 45 },
  ];

  return (
    <div className="re-card" style={{ paddingBottom: '8px' }}>
      <div className="re-card-header">{t('dashboardCards.rainfallTrend')}</div>
      <div style={{ height: '140px', width: '100%', marginLeft: '-20px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} ticks={[0, 40, 80, 120]} />
            <Tooltip cursor={{ fill: '#f1f5f9' }} />
            <Bar dataKey="rain" fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={16} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
