import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { MessageSquare, Send, AlertCircle } from 'lucide-react';
import api from '../utils/api';

export default function FarmerAdvisor({ selCell, forecast, decision, village }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim() || !selCell) return;
    
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await api.post('/api/v1/advisor/chat', {
        location_id: selCell,
        message: userMsg,
        language
      });
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.answer, mode: res.data.mode }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "System unavailable.", mode: 'OFFLINE' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '400px' }}>
      <div style={{ padding: '16px', borderBottom: '1px solid var(--line)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '16px', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MessageSquare size={18} /> AI Farmer Advisor
        </h2>
        <select value={language} onChange={e => setLanguage(e.target.value)} style={{ padding: '4px 8px', borderRadius: '4px', border: '1px solid var(--line)' }}>
          <option value="en">English</option>
          <option value="ta">Tamil</option>
          <option value="hi">Hindi</option>
        </select>
      </div>

      <div style={{ padding: '12px', background: 'var(--bg-body)', fontSize: '11px', color: 'var(--muted)', display: 'flex', gap: '8px', borderBottom: '1px solid var(--line)' }}>
        <AlertCircle size={14} />
        <div>
          Based on current system data:<br/>
          Location: {village?.name_en || selCell}<br/>
          Forecast: {forecast?.prediction?.status || 'Unknown'} | Decision: {decision?.action || 'Unknown'}
        </div>
      </div>

      <div style={{ flex: 1, padding: '16px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--muted)', fontSize: '13px', marginTop: '20px' }}>
            Ask a question like: "Should I sow now?" or "Why did the system recommend WAIT?"
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} style={{ alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '80%' }}>
            <div style={{
              background: m.role === 'user' ? 'var(--primary)' : 'var(--surface)',
              color: m.role === 'user' ? '#fff' : 'var(--ink)',
              padding: '10px 14px', borderRadius: '12px', fontSize: '14px', border: m.role === 'user' ? 'none' : '1px solid var(--line)'
            }}>
              {m.content}
            </div>
            {m.mode && m.mode !== 'LIVE' && (
              <div style={{ fontSize: '10px', color: 'var(--status-warn)', marginTop: '4px', textAlign: 'left' }}>
                {m.mode === 'DEMO' ? 'DEMO AI MODE — RESPONSE GENERATED LOCALLY' : 'AI ADVISOR UNAVAILABLE'}
              </div>
            )}
          </div>
        ))}
        {loading && <div style={{ alignSelf: 'flex-start', color: 'var(--muted)', fontSize: '12px' }}>Assistant is typing...</div>}
      </div>

      <div style={{ padding: '16px', borderTop: '1px solid var(--line)', display: 'flex', gap: '8px' }}>
        <input 
          value={input} onChange={e => setInput(e.target.value)} 
          onKeyDown={e => e.key === 'Enter' && handleSend()}
          placeholder="Ask about the monsoon recommendation..."
          style={{ flex: 1, padding: '10px', borderRadius: '8px', border: '1px solid var(--line)' }}
        />
        <button onClick={handleSend} disabled={loading} style={{ padding: '10px 16px', borderRadius: '8px', border: 'none', background: 'var(--primary)', color: 'white', cursor: 'pointer' }}>
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
