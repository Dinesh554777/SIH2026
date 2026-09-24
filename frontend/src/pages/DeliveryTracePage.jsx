import React, { useState, useEffect } from "react";
import { 
  Smartphone, MessageCircle, Phone, FileText, Users, 
  MapPin, CheckCircle, AlertTriangle, Clock, Send, Eye
} from "lucide-react";
import { motion } from 'framer-motion';
import { useLanguage } from "../context/LanguageContext.jsx";
import { api } from "../api.js";
import FarmerAdvisor from '../components/FarmerAdvisor';
import PredictionEvidence from '../components/PredictionEvidence';
import SystemEvidence from '../components/SystemEvidence';

function DeliveryChannelCard({ icon: Icon, name, description, status, recipients }) {
  const isReady = status === 'READY';
  const isDemo = status === 'DEMO MODE';
  const isConfig = status === 'CONFIGURATION REQUIRED';
  
  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ background: 'var(--bg-card)', padding: '10px', borderRadius: '12px', color: 'var(--primary)' }}>
            <Icon size={24} />
          </div>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', color: 'var(--ink)' }}>{name}</h3>
            <p style={{ margin: 0, fontSize: '12px', color: 'var(--muted)' }}>{description}</p>
          </div>
        </div>
      </div>
      
      <div style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '8px' }}>
        Recipients: <strong style={{ color: 'var(--ink)' }}>{recipients ?? 'Recipients not configured'}</strong>
      </div>
      
      <div style={{ 
        display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: '600',
        color: isReady || isDemo ? 'var(--status-onset)' : 'var(--status-low)'
      }}>
        <span style={{ fontSize: '14px' }}>{isReady || isDemo ? '●' : '⚠'}</span>
        {status}
      </div>
    </div>
  );
}

function AdvisoryComposer({ forecast, decision, village, onSend }) {
  const [selectedChannels, setSelectedChannels] = useState({ sms: true, whatsapp: true, print: false });
  const [language, setLanguage] = useState('ta');
  const [target, setTarget] = useState('farmers');
  const [phone, setPhone] = useState('');
  const [showPreview, setShowPreview] = useState(false);
  const [sending, setSending] = useState(false);

  const handleSend = () => {
    setSending(true);
    onSend({ channels: selectedChannels, language, target, phone, message: generateAdvisory() })
      .finally(() => {
        setSending(false);
        setShowPreview(false);
      });
  };

  const generateAdvisory = () => {
    if (language === 'en') {
      return `Monsoon update for ${village?.name_en || 'your location'}: Onset is ${forecast?.prediction?.status || 'Likely'}. Please ${decision?.action || 'WAIT'} before sowing. Next update: Tomorrow.`;
    }
    // Basic Tamil fallback for demo
    return `பருவமழை நிலவரம்: ${village?.name_ta || village?.name_en || 'உங்கள் பகுதி'}: நிலை ${forecast?.prediction?.status || 'சாத்தியம்'}. தயவுசெய்து விதைக்க ${decision?.action === 'WAIT' ? 'காத்திருக்கவும்' : 'தொடங்கவும்'}.`;
  };

  return (
    <div className="glass-panel" style={{ padding: '24px', gridColumn: 'span 2' }}>
      <h2 style={{ fontSize: '18px', marginBottom: '20px', color: 'var(--ink)' }}>Advisory Composer</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '20px', marginBottom: '24px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'var(--muted)', marginBottom: '8px' }}>Target Audience</label>
          <select value={target} onChange={e => setTarget(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--line)' }}>
            <option value="farmers">Farmers</option>
            <option value="fpo">FPO Groups</option>
            <option value="panchayat">Panchayat</option>
          </select>
        </div>
        
        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'var(--muted)', marginBottom: '8px' }}>Language</label>
          <select value={language} onChange={e => setLanguage(e.target.value)} style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--line)' }}>
            <option value="ta">Tamil (தமிழ்)</option>
            <option value="en">English</option>
            <option value="hi">Hindi (हिंदी)</option>
          </select>
        </div>

        <div>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'var(--muted)', marginBottom: '8px' }}>Test Phone Number</label>
          <input type="text" value={phone} onChange={e => setPhone(e.target.value)} placeholder="+919876543210" style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid var(--line)' }} />
        </div>
      </div>

      <div style={{ marginBottom: '24px' }}>
        <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'var(--muted)', marginBottom: '12px' }}>Delivery Channels</label>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          {['sms', 'whatsapp', 'ivr', 'print'].map(ch => (
            <label key={ch} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input type="checkbox" checked={selectedChannels[ch] || false} onChange={e => setSelectedChannels({...selectedChannels, [ch]: e.target.checked})} />
              <span style={{ textTransform: 'uppercase', fontSize: '13px', fontWeight: '500' }}>{ch}</span>
            </label>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '12px' }}>
        <button onClick={() => setShowPreview(!showPreview)} style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid var(--line)', background: 'transparent', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '600' }}>
          <Eye size={16} /> Preview Advisory
        </button>
      </div>

      {showPreview && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ marginTop: '20px', padding: '16px', background: 'var(--bg-body)', borderRadius: '8px', border: '1px solid var(--line)' }}>
          <h4 style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--muted)', marginBottom: '12px' }}>Preview</h4>
          <p style={{ margin: 0, fontSize: '15px', color: 'var(--ink)', lineHeight: '1.5' }}>{generateAdvisory()}</p>
          <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end' }}>
            <button onClick={handleSend} disabled={sending} style={{ padding: '10px 24px', borderRadius: '8px', border: 'none', background: 'var(--primary)', color: 'white', cursor: sending ? 'wait' : 'pointer', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '600' }}>
              {sending ? <Clock size={16} /> : <Send size={16} />} 
              {sending ? 'Sending...' : 'Send Advisory'}
            </button>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--status-likely)', textAlign: 'right', marginTop: '8px' }}>
            {phone ? 'LIVE DELIVERY INITIATED' : 'DEMO MODE — NO REAL MESSAGE SENT'}
          </div>
        </motion.div>
      )}
    </div>
  );
}

import PrintableAdvisory from '../components/PrintableAdvisory';

export default function DeliveryTracePage({ cells, selCell, village, forecast, decision }) {
  const { t } = useLanguage();
  const [history, setHistory] = useState([]);
  const [printData, setPrintData] = useState(null);

  const handleSend = async (payload) => {
    try {
      const res = await api.post("/api/v1/delivery/send", payload);
      const data = res.data;
      
      const newJob = {
        id: data.job_id,
        date: new Date().toLocaleString(),
        channels: Object.keys(payload.channels).filter(k => payload.channels[k]).join(', '),
        audience: payload.target,
        status: data.status
      };
      
      setHistory(prev => [newJob, ...prev]);

      // If print was selected, show the print modal
      if (payload.channels.print) {
        setPrintData(true);
      }

      // Poll for status
      const interval = setInterval(async () => {
        try {
          const statusRes = await api.get(`/api/v1/delivery/status/${data.job_id}`);
          setHistory(prev => prev.map(job => 
            job.id === data.job_id ? { ...job, status: statusRes.data.status } : job
          ));
          if (statusRes.data.status === 'SENT' || statusRes.data.status === 'DEMO SIMULATED' || statusRes.data.status === 'FAILED') {
            clearInterval(interval);
          }
        } catch (e) {
          clearInterval(interval);
        }
      }, 2000);
      
    } catch (err) {
      console.error(err);
      alert("Failed to queue delivery.");
    }
  };

  return (
    <main className="page-content" style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      {printData && (
        <PrintableAdvisory 
          forecast={forecast} 
          decision={decision} 
          village={village} 
          onClose={() => setPrintData(null)} 
        />
      )}

      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '24px', margin: '0 0 8px 0', color: 'var(--ink)' }}>Delivery Channels</h1>
        <p style={{ margin: 0, color: 'var(--muted)', fontSize: '15px' }}>Reach farmers through the communication channel available to them.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '32px' }}>
        <DeliveryChannelCard name="SMS" icon={Smartphone} description="Farmer alerts & advisories" status="DEMO MODE" recipients={null} />
        <DeliveryChannelCard name="WhatsApp" icon={MessageCircle} description="Rich media alerts" status="CONFIGURATION REQUIRED" recipients={null} />
        <DeliveryChannelCard name="IVR" icon={Phone} description="Voice calls for accessibility" status="CONFIGURATION REQUIRED" recipients={null} />
        <DeliveryChannelCard name="Print Notice" icon={FileText} description="Physical community board" status="READY" recipients="Panchayat Offices" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <AdvisoryComposer forecast={forecast} decision={decision} village={village} onSend={handleSend} />
          <FarmerAdvisor selCell={selCell} forecast={forecast} decision={decision} village={village} />
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <PredictionEvidence forecast={forecast} decision={decision} />
          
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ fontSize: '18px', marginBottom: '20px', color: 'var(--ink)' }}>Delivery History</h2>
            {history.length === 0 ? (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontSize: '13px' }}>
                No delivery data available.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {history.map(h => (
                  <div key={h.id} style={{ borderBottom: '1px solid var(--line)', paddingBottom: '12px' }}>
                    <div style={{ fontSize: '11px', color: 'var(--muted)' }}>{h.date}</div>
                    <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--ink)', margin: '4px 0' }}>{h.channels.toUpperCase()} • {h.audience}</div>
                    <div style={{ fontSize: '12px', color: 'var(--status-likely)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <CheckCircle size={12} /> {h.status}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <SystemEvidence forecast={forecast} decision={decision} />
        </div>
      </div>
    </main>
  );
}
