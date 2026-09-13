const FO_COPY = {
  low: {
    note: "No early-rain false-start is being signalled; the onset state is only treated as sustained once the 7-day wet-day rule is met.",
    window: "ongoing — re-check after each new rainfall observation",
  },
  medium: {
    note: "Partial wet-day signal only; the onset state is not yet sustained. Re-check after the next rainfall observation before committing seed.",
    window: "ongoing — re-check after each new rainfall observation",
  },
  high: {
    note: "Recent rainfall looks like a false start (rain was not followed by the sustained wet-day rule). Hold sowing until the rule is met.",
    window: "hold — wake up to re-check after each new rainfall observation",
  },
};

const RISK_STYLE = {
  low: "low",
  medium: "med",
  high: "high",
  critical: "critical",
  moderate: "med",
};

export default function RiskCards({ decision, advisory, village }) {
  if (!decision) return null;
  const risk = decision.risk_summary ?? {};
  const item = (state) => advisory?.items?.find((i) => i.state === state);
  const safe = (v, d) => (v != null ? v : d);

  const dryItem = item("dry_spell");
  const breakItem = item("break");
  const fo = decision.false_onset_risk ?? "low";
  const dryFixture = risk.dry_spell;
  const breakFixture = risk.break;

  const dry = {
    band: dryFixture?.band ?? "low",
    pct: Math.round((dryFixture?.probability ?? 0) * 100),
    interpretation: dryItem?.interpretation ?? "Dry conditions are indicated in the current model state.",
    action: dryItem?.suggested_action ?? "Follow the officer action for water conservation.",
    detail: safe(
      advisory?.current_signal?.dry_streak_days != null
        ? `${advisory.current_signal.dry_streak_days} day(s) dry so far`
        : null,
      "running dry spell — re-check daily"
    ),
  };
  const bre = {
    band: breakFixture?.band ?? "low",
    pct: Math.round((breakFixture?.probability ?? 0) * 100),
    interpretation: breakItem?.interpretation ?? "A dry interruption is indicated in the current model state.",
    action: breakItem?.suggested_action ?? "Follow the officer action for water conservation.",
    detail: "day-by-day — probability describes today's state",
  };
  const foCard = {
    level: fo,
    note: FO_COPY[fo]?.note ?? FO_COPY.low.note,
    window: FO_COPY[fo]?.window ?? FO_COPY.low.window,
  };

  return (
    <section className="panel risk-cards-panel" data-testid="risk-cards">
      <div className="kicker">4 · Risk analysis</div>
      <h2>What could go wrong next?</h2>
      <div className="risk-cards">
        <article className="risk-card" data-testid="risk-card-false-onset">
          <div className="risk-card-head">
            <span className="risk-card-title">False onset</span>
            <span className={`risk-chip chip-fo chip-fo-${foCard.level}`}>{foCard.level}</span>
          </div>
          <p className="risk-card-note">{foCard.note}</p>
          <p className="risk-card-window">Window · {foCard.window}</p>
          <p className="risk-card-action">
            Recommended action · wait for the sustained wet-day rule before sowing.
          </p>
        </article>

        <article className="risk-card" data-testid="risk-card-dry-spell">
          <div className="risk-card-head">
            <span className="risk-card-title">Dry spell</span>
            <span className={`risk-chip chip-risk-${RISK_STYLE[dry.band]}`}>
              {dry.pct}% · {dry.band}
            </span>
          </div>
          <p className="risk-card-note">{dry.interpretation}</p>
          <p className="risk-card-window">Window · {dry.detail}</p>
          <p className="risk-card-action">Recommended action · {dry.action}</p>
        </article>

        <article className="risk-card" data-testid="risk-card-break">
          <div className="risk-card-head">
            <span className="risk-card-title">Break</span>
            <span className={`risk-chip chip-risk-${RISK_STYLE[bre.band]}`}>
              {bre.pct}% · {bre.band}
            </span>
          </div>
          <p className="risk-card-note">{bre.interpretation}</p>
          <p className="risk-card-window">Window · {bre.detail}</p>
          <p className="risk-card-action">Recommended action · {bre.action}</p>
        </article>
      </div>
      {village && <p className="muted">Serving block · {village.name}</p>}
      <p className="muted">Risk levels are derived from frozen model probabilities and the officer decision engine — not fabricated staff estimates.</p>
    </section>
  );
}
