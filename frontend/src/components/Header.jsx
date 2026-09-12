const LANGS = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "ta", label: "தமிழ்" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "mr", label: "मराठी" },
];

export default function Header({ modelInfo, lang, setLang }) {
  return (
    <header className="header">
      <div className="header-title">
        <h1>Hyperlocal Monsoon Decision Support</h1>
        <p className="subtitle">
          Probabilistic agricultural decision support from monsoon signals
        </p>
      </div>
      <div className="header-meta">
        <label className="lang-field">
          <span>Explain in</span>
          <select value={lang} onChange={(e) => setLang(e.target.value)}>
            {LANGS.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
        </label>
        <span className="chip chip-dark" title="Frozen model artifact">
          Model {modelInfo?.model_version ?? "…"}
        </span>
        <span className="chip" title="Backend serving mode">
          {modelInfo?.data_mode ?? "…"} mode
        </span>
      </div>
    </header>
  );
}