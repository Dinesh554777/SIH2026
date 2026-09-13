import { useState } from "react";
import { api } from "../api";
import { ShieldAlert, Phone, Users, FileText, UserCheck } from 'lucide-react';
import VoicePlayer from './voice/VoicePlayer.jsx';

const CHANNELS = [
  { key: "sms", label: "SMS", icon: Phone },
  { key: "whatsapp", label: "WhatsApp", icon: Phone },
  { key: "ivr", label: "IVR call", icon: Phone },
  { key: "notice_print", label: "Print Notice", icon: FileText },
  { key: "field_worker", label: "Field worker", icon: UserCheck },
  { key: "panchayat", label: "Panchayat", icon: Users },
  { key: "fpo", label: "FPO group", icon: Users },
];

export default function VillageAdvisoryPanel({ cellId, date, decision, village, issuedBy, crop }) {
  const [advisory, setAdvisory] = useState(null);
  const [lang, setLang] = useState("en");
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(null);
  const [delivery, setDelivery] = useState(null);
  const [generating, setGenerating] = useState(false);

  const generate = async () => {
    setGenerating(true);
    setDelivery(null);
    try {
      const r = await api.villageAdvisory(cellId, date, {
        crop: crop || "paddy",
        season: "kharif",
        villageName: village?.name || "Demo Village",
        villageId: village?.village_id || "TN-ORA-001",
      });
      setAdvisory(r.advisory ?? r);
    } catch {
      setAdvisory(null);
    } finally {
      setGenerating(false);
    }
  };

  const send = async (channel) => {
    setSending(channel);
    setDelivery(null);
    try {
      const r = await api.deliver(cellId, date, { channel, crop: crop || "paddy", issuedBy });
      setDelivery(r);
    } catch {
      setDelivery(null);
    } finally {
      setSending(null);
    }
  };

  const v = advisory?.messages?.[lang] ?? advisory?.messages?.en;

  return (
    <div className="field-note-panel">
      <div className="fn-header">
        <span>LAST-MILE ADVISORY</span>
        <select
          value={lang}
          onChange={(e) => setLang(e.target.value)}
          className="fn-lang-select"
          data-testid="advisory-lang"
        >
          <option value="en">EN</option>
          <option value="ta">TA</option>
        </select>
      </div>

      {!v ? (
        <div className="fn-empty">
          <p>Generate a localized field advisory for {village ? village.name : 'the selected region'}.</p>
          <button className="fn-btn-primary" onClick={generate} disabled={generating}>
            {generating ? "Generating..." : "Generate Advisory"}
          </button>
        </div>
      ) : (
        <div className="fn-content">
          <div className="advisory-preview" data-testid="advisory-preview">
            <div className="ap-line">VILLAGE: <strong>{advisory?.village_name ?? v.print_head?.match(/VILLAGE:\s*([^\n|]+)/i)?.[1] ?? village?.name ?? "Demo Village"}</strong></div>
            <div className="ap-line">DATE: {advisory?.issue_date ?? date ?? "—"}</div>
            <div className="ap-line">MONSOON STATUS: {advisory?.monsoon_status_label ?? "—"}</div>
            <div className="ap-line">ACTION: {advisory?.decision_label ?? "—"}</div>
            <h3 className="fn-title">{v.title}</h3>
            <pre className="fn-text">{v.print_head ?? v.block}</pre>
          </div>

          <div className="fn-actions" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <VoicePlayer text={v.block} lang={lang} />
            <button className="fn-btn-secondary" onClick={generate} disabled={generating}>
              Regenerate
            </button>
          </div>

          <div className="fn-delivery">
            <div className="fn-subtitle">DELIVERY CHANNELS</div>
            <div className="fn-channels">
              {CHANNELS.map((c) => (
                <button
                  key={c.key}
                  className="fn-channel-btn"
                  onClick={() => send(c.key)}
                  disabled={sending === c.key}
                >
                  <c.icon size={16} />
                  <span>{sending === c.key ? "..." : c.label}</span>
                </button>
              ))}
            </div>
          </div>

          {delivery && (
            <div className="fn-receipt" data-testid="delivery-result">
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#10b981', fontWeight: 600, marginBottom: 8 }}>
                <ShieldAlert size={16} /> Delivery Confirmed
              </div>
              <div style={{ fontSize: '0.8rem', color: '#475569' }}>
                <div><strong>Channel:</strong> {delivery.channel}</div>
                <div><strong>Message:</strong> {delivery.delivery?.message}</div>
                {delivery.delivery?.mock_notice && (
                  <div style={{ marginTop: 4 }}>{delivery.delivery.mock_notice}</div>
                )}
                {delivery.delivery?.via && (
                  <div style={{ marginTop: 4 }}><strong>Via:</strong> {delivery.delivery.via}</div>
                )}
                {delivery.traceability && (
                  <div style={{ marginTop: 4, fontFamily: 'monospace', fontSize: '0.75rem', background: '#f1f5f9', padding: 4, borderRadius: 4 }}>
                    delivery # {delivery.traceability.delivery_id}{" "}
                    (Persisted: {String(delivery.traceability?.persisted)}){" "}
                    risk_assessment # {delivery.traceability.risk_assessment_id}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}