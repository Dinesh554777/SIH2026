import { useState } from "react";
import { api } from "../api";

const CHANNELS = [
  { key: "notice_print", label: "Notice / print" },
  { key: "sms", label: "SMS" },
  { key: "whatsapp", label: "WhatsApp" },
  { key: "ivr", label: "IVR call" },
  { key: "field_worker", label: "Field worker" },
  { key: "panchayat", label: "Panchayat" },
  { key: "fpo", label: "FPO group" },
];

export default function VillageAdvisoryPanel({ cellId, date, decision, village, issuedBy }) {
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
        crop: "paddy",
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
      const r = await api.deliver(cellId, date, { channel, crop: "paddy", issuedBy });
      setDelivery(r);
    } catch {
      setDelivery(null);
    } finally {
      setSending(null);
    }
  };

  const v = advisory?.messages?.[lang] ?? advisory?.messages?.en;

  return (
    <section className="panel advisory-village" id="advisory">
      <div className="kicker">5 · Last-mile village advisory</div>
      <h2>Village advisory & delivery</h2>
      <p className="muted">
        Bilingual advisory derived from the frozen model + the decision above. Printed
        A4 layouts, SMS/WhatsApp text, IVR scripts and field-worker sheets are generated
        for the officer below the grid cell resolution wherever a village is selected.
      </p>

      <div className="village-toolbar">
        <button className="btn btn-primary" onClick={generate} disabled={generating}>
          {generating ? "Generating…" : advisory ? "Regenerate advisory" : "Generate advisory"}
        </button>
        <select
          value={lang}
          onChange={(e) => setLang(e.target.value)}
          aria-label="Advisory language"
          data-testid="advisory-lang"
        >
          <option value="en">English</option>
          <option value="ta">தமிழ்</option>
        </select>
      </div>

      {loading ? (
        <p className="muted">Loading…</p>
      ) : v ? (
        <div className="advisory-output">
          <div className="advisory-tabs" aria-label="Advisory preview">
            <div className="advisory-preview" data-testid="advisory-preview">
              <h3>{v.title}</h3>
              <pre className="print-block">{v.print_head ?? v.block}</pre>
              <details>
                <summary>Plain offline text</summary>
                <pre className="plain-block">{v.block}</pre>
              </details>
            </div>
          </div>

          <div className="channel-grid" data-testid="channel-grid">
            {CHANNELS.map((c) => (
              <button
                key={c.key}
                className="channel-btn"
                onClick={() => send(c.key)}
                disabled={sending === c.key}
              >
                {sending === c.key ? "Sending…" : c.label}
              </button>
            ))}
          </div>

          {delivery && (
            <div className="delivery-result" data-testid="delivery-result">
              <h4>
                {delivery.channel} · MOCK gateway
              </h4>
              <p className="delivery-message">{delivery.delivery?.message}</p>
              <p className="delivery-mock">{delivery.delivery?.mock_notice}</p>
              <div className="trace-row">
                {delivery.traceability?.risk_assessment_id != null && (
                  <span>risk_assessment # {delivery.traceability.risk_assessment_id}</span>
                )}
                {delivery.traceability?.delivery_id != null && (
                  <span>delivery # {delivery.traceability.delivery_id}</span>
                )}
                <span>db {delivery.traceability?.database}</span>
                <span>persisted {String(delivery.traceability?.persisted)}</span>
              </div>
              {delivery.delivery?.ivr_script && (
                <pre className="ivr-script">{delivery.delivery.ivr_script}</pre>
              )}
            </div>
          )}
        </div>
      ) : (
        <p className="muted" data-testid="advisory-empty">
          No advisory generated yet (no fabricated numbers are shown before model output).
        </p>
      )}
    </section>
  );
}