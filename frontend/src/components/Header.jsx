const LANGS = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "ta", label: "தமிழ்" },
  { code: "kn", label: "ಕನ್ನಡ" },
  { code: "mr", label: "मराठी" },
];

const NAV = [
  { id: "dashboard", label: "Dashboard" },
  { id: "map", label: "Map" },
  { id: "forecast", label: "Forecast" },
  { id: "advisory", label: "Advisory" },
  { id: "analytics", label: "Analytics" },
  { id: "alerts", label: "Alerts" },
];

export function Logo({ size = 34 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      aria-hidden="true"
      className="logo-mark"
    >
      <path
        d="M24 44C13 34 8 26 8 18a16 16 0 0 1 32 0c0 8-5 16-16 26Z"
        fill="#0f766e"
      />
      <path d="M24 20c-3.5-2.5-5-5-5-7a5 5 0 0 1 10 0c0 2-1.5 4.5-5 7Z" fill="#ccfbf1" />
      <path d="M18 26h12M18 30h9" stroke="#134e4a" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export default function Header({ modelInfo, lang, setLang, scrolled }) {
  const go = (id) => (e) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <header className={`header ${scrolled ? "header-scrolled" : ""}`}>
      <div className="header-inner">
        <a className="brand" href="#dashboard" onClick={go("dashboard")}>
          <Logo />
          <span className="brand-text">
            <span className="brand-name">Hyperlocal Monsoon</span>
            <span className="brand-sub">Probabilistic agricultural decision support</span>
          </span>
        </a>

        <h1 className="sr-only">Hyperlocal Monsoon Decision Support</h1>

        <nav className="nav-links" aria-label="Primary">
          {NAV.map((n) => (
            <a key={n.id} className="nav-link" href={`#${n.id}`} onClick={go(n.id)}>
              {n.label}
            </a>
          ))}
        </nav>

        <div className="header-meta">
          <label className="lang-field">
            <span>Explain in</span>
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              aria-label="Explanation language"
            >
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
      </div>
    </header>
  );
}
