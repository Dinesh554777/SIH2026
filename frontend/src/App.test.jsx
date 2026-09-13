import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { api } from "./api.js";
import App from "./App.jsx";
import {
  advisoryFixture,
  cellsFixture,
  decisionFixture,
  deliveryFixture,
  explainFixture,
  explanationFixture,
  explanationGroqFixture,
  forecastFixture,
  geographyDemoFixture,
  modelInfoFixture,
  scenariosFixture,
  villageAdvisoryFixture,
} from "./test/fixtures.js";

function ok(body) {
  return { ok: true, status: 200, json: async () => body };
}

function httpError(status, body = {}) {
  return { ok: false, status, json: async () => body };
}

/**
 * Fetch mock speaking only to fixtures. Options:
 *  - forecastError: the forecast route 404s with error.code unknown_cell
 *  - rejectAll: every request rejects (backend unavailable)
 *  - groq: the explanation route returns a source:groq payload
 *  - delayForecast: promise awaited before the forecast resolves (loading test)
 */
function installApi({
  forecastError = false,
  missingForecast = false,
  serverError = false,
  malformedForecast = false,
  rejectAll = false,
  groq = false,
  delayForecast = null,
} = {}) {
  const calls = [];
  const handler = (input) => {
    const url = typeof input === "string" ? input : input.url;
    calls.push(url);
    if (rejectAll) {
      return Promise.reject(new TypeError("NetworkError when attempting to fetch resource."));
    }
    const path = new URL(url, "http://test.local").pathname;
    const respond = (body) =>
      Promise.resolve(delayForecast && path.endsWith("/forecast") ? delayForecast.then(() => ok(body)) : ok(body));
    if (path === "/api/v1/cells") return Promise.resolve(ok(cellsFixture()));
    if (path === "/api/v1/model-info") return Promise.resolve(ok(modelInfoFixture));
    if (path === "/api/v1/geography/demo") return Promise.resolve(ok(geographyDemoFixture));
    if (path === "/api/v1/demo/scenarios") return Promise.resolve(ok(scenariosFixture));
    const m = path.match(
      /^\/api\/v1\/cells\/([^/]+)\/(forecast|explain|explanation|advisory|decision|village-advisory|deliver)$/
    );
    if (m) {
      const [, , kind] = m;
      if (kind === "forecast") {
        if (forecastError) {
          return Promise.resolve(httpError(404, { error: { code: "unknown_cell", message: "Unknown grid cell." } }));
        }
        if (missingForecast) {
          return Promise.resolve(
            httpError(404, { error: { code: "date_not_available", message: "No observations for this cell on the date." } })
          );
        }
        if (serverError) {
          return Promise.resolve(httpError(500, { error: { code: "internal", message: "boom" } }));
        }
        if (malformedForecast) {
          return Promise.resolve({
            ok: true,
            status: 200,
            json: async () => {
              throw new SyntaxError("Unexpected end of JSON input");
            },
          });
        }
      }
      const data = {
        forecast: forecastFixture,
        explain: explainFixture,
        explanation: groq ? explanationGroqFixture : explanationFixture,
        advisory: advisoryFixture,
        decision: { decision: decisionFixture },
        "village-advisory": { advisory: villageAdvisoryFixture.advisory, ...villageAdvisoryFixture },
        deliver: deliveryFixture,
      }[kind];
      return respond(data);
    }
    return Promise.resolve(httpError(404, { error: { code: "not_found", message: "not found" } }));
  };
  const fetchMock = vi.fn(handler);
  vi.stubGlobal("fetch", fetchMock);
  return { fetchMock, calls };
}

describe("Hyperlocal Monsoon Decision Support frontend", () => {
  it("renders header with the project title", async () => {
    installApi();
    render(<App />);
    expect(
      await screen.findByRole("heading", { name: "Hyperlocal Monsoon Decision Support" })
    ).toBeInTheDocument();
    expect(screen.getByText(/Probabilistic agricultural decision support/i)).toBeInTheDocument();
  });

  it("shows the HISTORICAL / DEMO MODE banner and never claims live", async () => {
    installApi();
    render(<App />);
    await screen.findByText(/Dry spell probability is 92%/i);
    const banner = screen.getByText(/HISTORICAL \/ DEMO MODE/i).closest(".demo-banner");
    expect(banner).toHaveTextContent(/historical-model demonstrations/i);
    // the banner explicitly negates any claim of a live forecast
    expect(banner.textContent).toMatch(/not live forecasts/);
    expect(banner.textContent).not.toMatch(/(?<!not )live forecasts/);
  });

  it("lists 304 pilot grid cells and pre-selects a location", async () => {
    installApi();
    render(<App />);
    const select = await screen.findByTestId("cell-select");
    await waitFor(() => expect(select.options.length).toBe(304));
    expect(select.value).toBe("10.75_77.5");
    await waitFor(() =>
      expect(screen.getByTestId("cell-meta")).toHaveTextContent("10.75_77.5")
    );
    expect(screen.getByTestId("cell-meta")).toHaveTextContent("Tamil Nadu");
  });

  it("shows a loading state while the forecast is being requested", async () => {
    let release;
    const gate = new Promise((r) => (release = r));
    installApi({ delayForecast: gate });
    render(<App />);
    await screen.findByText("Requesting forecast…");
    expect(screen.getByRole("status")).toBeInTheDocument();
    release();
    await screen.findByText(/Dry spell probability is 92%/i);
  });

  it("renders the four probability cards from real API values", async () => {
    installApi();
    render(<App />);
    for (const t of ["onset", "break", "revival", "dry_spell"]) {
      const card = await screen.findByTestId(`card-${t}`);
      expect(card).toBeInTheDocument();
    }
    expect(await screen.findByText("90.8%")).toBeInTheDocument();
    expect(screen.getByText("60.5%")).toBeInTheDocument();
    expect(screen.getByText("91.6%")).toBeInTheDocument();
    expect(screen.getByText(/Unlikely · low/i)).toBeInTheDocument();
    expect(within(screen.getByTestId("card-break")).getByText(/Very likely · very high/i)).toBeInTheDocument();
    expect(
      within(screen.getByTestId("card-dry_spell")).getByText(/Near-term dry conditions are strongly indicated/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/not accuracy and not certainty/i)).toBeInTheDocument();
  });

  it("shows current-signal chips from observed inputs", async () => {
    installApi();
    render(<App />);
    await screen.findByText(/Dry spell probability is 92%/i);
    expect(screen.getByTestId("signal-rain_t_mm")).toHaveTextContent("2.97 mm");
    expect(screen.getByTestId("signal-dry_streak_days")).toHaveTextContent("26 days");
    expect(screen.getByTestId("signal-rainfall_regime")).toHaveTextContent("Drying");
  });

  it("shows the advisory blocks + deterministic fallback badge when Groq is down", async () => {
    installApi();
    render(<App />);
    await screen.findByText(/Dry spell probability is 92%/i);
    for (const heading of [
      "What is happening?",
      "What does it mean?",
      "What should the user consider?",
    ]) {
      expect(screen.getByRole("heading", { name: heading })).toBeInTheDocument();
    }
    expect(screen.getByTestId("advisory-source")).toHaveTextContent("Deterministic advisory");
    expect(screen.getByText(/Groq was unavailable/i)).toBeInTheDocument();
    expect(screen.getByTestId("dominant-callout")).toHaveTextContent(/dry spell/i);
  });

  it("shows the Groq badge when the backend explanation is generated by Groq", async () => {
    installApi({ groq: true });
    render(<App />);
    await screen.findByText(/Dry spell and break probabilities are elevated/i);
    expect(screen.getByTestId("advisory-source")).toHaveTextContent("Groq explanation");
    expect(screen.getByText(/Generated by llama-3.3-70b-versatile/i)).toBeInTheDocument();
  });

  it("labels the Why section as model sensitivity, not causal explanation", async () => {
    installApi();
    render(<App />);
    await screen.findByText(/Dry spell probability is 92%/i);
    expect(screen.getByTestId("sensitivity-caveat")).toHaveTextContent(
      "Model sensitivity — not causal explanation"
    );
    expect(screen.getByRole("heading", { name: "Why this forecast?" })).toBeInTheDocument();
  });

  it("shows model transparency: model, feature group, periods, mode", async () => {
    installApi();
    render(<App />);
    await screen.findByText(/Dry spell probability is 92%/i);
    expect(screen.getByRole("heading", { name: "Model transparency" })).toBeInTheDocument();
    expect(screen.getByText("xgboost")).toBeInTheDocument();
    expect(screen.getByText("B_temporal")).toBeInTheDocument();
    expect(screen.getByTestId("transparency-mode")).toHaveTextContent("historical/demo");
    expect(screen.getByText("2015-2021")).toBeInTheDocument();
    expect(screen.getByText("4f122044f8710b53")).toBeInTheDocument();
  });

  it("shows the calibration statement and validation metrics", async () => {
    installApi();
    render(<App />);
    await screen.findByText(/Dry spell probability is 92%/i);
    expect(
      screen.getByText(/Probabilities represent estimated likelihood, not certainty/i)
    ).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Calibration" })).toBeInTheDocument();
    expect(screen.getAllByText("2022-2023").length).toBeGreaterThanOrEqual(4);
  });

  it("lets the user pick another cell and refetches that cell's forecast", async () => {
    const { calls } = installApi();
    const user = userEvent.setup();
    render(<App />);
    await waitFor(() => expect(screen.getByTestId("cell-select").options.length).toBe(304));
    await user.selectOptions(screen.getByTestId("cell-select"), "10.0_76.25");
    expect(screen.getByTestId("cell-meta")).toHaveTextContent("10.0_76.25");
    await waitFor(() =>
      expect(calls.some((u) => u.includes("/api/v1/cells/10.0_76.25/forecast"))).toBe(true)
    );
  });

  it("shows an understandable error panel for an invalid cell", async () => {
    installApi({ forecastError: true });
    render(<App />);
    const panel = await screen.findByTestId("error-panel");
    expect(panel).toHaveTextContent("Invalid grid cell");
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
  });

  it("shows an understandable error panel when the backend is unavailable", async () => {
    installApi({ rejectAll: true });
    render(<App />);
    const panel = await screen.findByTestId("error-panel");
    expect(panel).toHaveTextContent("Backend unavailable");
    expect(panel).toHaveTextContent(/Start the API server/i);
  });

  it("shows an understandable error panel for a missing forecast date", async () => {
    installApi({ missingForecast: true });
    render(<App />);
    const panel = await screen.findByTestId("error-panel");
    expect(panel).toHaveTextContent("No forecast available");
    expect(panel).toHaveTextContent(/no observations/i);
  });

  it("shows an understandable error panel for a backend 500", async () => {
    installApi({ serverError: true });
    render(<App />);
    const panel = await screen.findByTestId("error-panel");
    expect(panel).toHaveTextContent("Backend error");
    expect(panel).toHaveTextContent(/internal error/i);
    expect(panel).toHaveTextContent(/boom/i);
  });

  it("shows an understandable error panel for a malformed (non-JSON) response", async () => {
    installApi({ malformedForecast: true });
    render(<App />);
    const panel = await screen.findByTestId("error-panel");
    expect(panel).toHaveTextContent("Malformed API response");
    expect(panel).toHaveTextContent(/unexpected payload/i);
  });

  it("maps a request timeout to a clear error code", async () => {
    vi.useFakeTimers();
    try {
      vi.stubGlobal(
        "fetch",
        vi.fn((_url, { signal }) =>
          new Promise((_resolve, reject) => {
            signal.addEventListener("abort", () =>
              reject(Object.assign(new Error("aborted"), { name: "AbortError" }))
            );
          })
        )
      );
      const p = api.forecast("10.75_77.5", "2024-08-12");
      // mark handled so vitest does not report an unhandled rejection
      const observed = p.then(
        () => null,
        (e) => e
      );
      await vi.advanceTimersByTimeAsync(13000);
      const err = await observed;
      expect(err).toMatchObject({ code: "timeout" });
      expect(err.message).toContain("timed out");
    } finally {
      vi.useRealTimers();
    }
  });

  it("renders no fabricated probabilities before a backend response arrives", async () => {
    installApi({ delayForecast: new Promise(() => {}) });
    render(<App />);
    expect(screen.queryByText("100%")).not.toBeInTheDocument();
    expect(screen.queryByTestId("card-onset")).not.toBeInTheDocument();
  });

  it("browses the demo hierarchy and resolves a village to its pilot cell decision", async () => {
    const { calls } = installApi();
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText(/Dry spell probability is 92%/i);

    await user.click(screen.getByRole("button", { name: /tamil nadu/i }));
    await user.click(screen.getByRole("button", { name: /thanjavur/i }));
    await user.click(screen.getByRole("button", { name: /orathanadu/i }));
    await user.click(screen.getByRole("button", { name: /demo rainfed village/i }));

    await waitFor(() =>
      expect(screen.getByTestId("cell-meta")).toHaveTextContent("10.0_76.25")
    );
    expect(screen.getByTestId("cell-meta")).toHaveTextContent("Demo Rainfed Village");
    expect(screen.getByTestId("status-where")).toHaveTextContent("Demo Rainfed Village");
    await waitFor(() =>
      expect(calls.some((u) => u.includes("/api/v1/cells/10.0_76.25/decision"))).toBe(true)
    );
  });

  it("renders the officer decision card with action badge and risk summary", async () => {
    installApi();
    render(<App />);
    await screen.findByText(/Dry spell probability is 92%/i);
    expect(screen.getByTestId("status-hero")).toHaveTextContent("Dry-spell risk");
    const card = screen.getByTestId("decision-card");
    expect(card).toHaveTextContent("Irrigation prepare");
    expect(within(card).getByTestId("risk-dry_spell")).toHaveTextContent("92% · high");
    expect(within(card).getByTestId("risk-onset")).toHaveTextContent("1% · low");
    expect(
      screen.getAllByText(/Decision-support suggestion, not a professional.*guarantee/i).length
    ).toBeGreaterThan(0);
  });

  it("generates a bilingual village advisory and shows MOCK delivery traceability", async () => {
    const { calls } = installApi();
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText(/Dry spell probability is 92%/i);

    await user.click(screen.getByRole("button", { name: /generate advisory/i }));
    expect(await screen.findByTestId("advisory-preview")).toHaveTextContent("VILLAGE:");
    expect(screen.getByTestId("advisory-preview")).toHaveTextContent("Demo Rainfed Village");
    await user.selectOptions(screen.getByTestId("advisory-lang"), "ta");
    expect(screen.getByTestId("advisory-preview")).toHaveTextContent(/ஊர்/);

    await user.click(screen.getByRole("button", { name: "SMS" }));
    await waitFor(() => expect(calls.some((u) => u.includes("deliver") && u.includes("channel=sms"))).toBe(true));
    const result = await screen.findByTestId("delivery-result");
    expect(result).toHaveTextContent("[MOCK SMS]");
    expect(result).toHaveTextContent("delivery # 7");
    expect(result).toHaveTextContent("risk_assessment # 12");
    expect(result).toHaveTextContent("MOCK gateway");
  });

  it("replays a frozen scenario date and recomputes the decision", async () => {
    const { calls } = installApi();
    const user = userEvent.setup();
    render(<App />);
    await screen.findByText(/Dry spell probability is 92%/i);
    expect(screen.getByTestId("scenario-strip")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /2024-06-07.*false onset/i }));
    await waitFor(() =>
      expect(calls.some((u) => u.includes("/decision?date=2024-06-07"))).toBe(true)
    );
    await waitFor(() =>
      expect(calls.some((u) => u.includes("/forecast?date=2024-06-07"))).toBe(true)
    );
  });
});