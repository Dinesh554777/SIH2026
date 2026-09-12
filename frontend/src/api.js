// Thin fetch wrapper around the FastAPI backend. Every request aborts itself
// after TIMEOUT_MS so the UI never hangs; the error thrown carries a stable
// `code` that the UI maps to a human-readable state.
const API_BASE = import.meta.env.VITE_API_BASE ?? "";
const TIMEOUT_MS = 12000;

export function request(path, { signal, timeoutMs = TIMEOUT_MS } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const onAbort = () => controller.abort();
  if (signal) {
    if (signal.aborted) controller.abort();
    else signal.addEventListener("abort", onAbort);
  }
  let res;
  return (
    fetch(`${API_BASE}${path}`, { signal: controller.signal })
      .then((r) => {
        res = r;
        return r;
      })
      .catch((err) => {
        if (err && (err.name === "AbortError")) {
          throw Object.assign(new Error("The request timed out."), { code: "timeout" });
        }
        if (err && err.code === "http_reject") throw err;
        throw Object.assign(
          new Error("The backend is unavailable. Start the API server and retry."),
          { code: "backend_unavailable" }
        );
      })
      .then(async (r) => {
        if (r.ok) return r.json();
        let detail = null;
        try {
          detail = await r.json();
        } catch {
          /* non-JSON error body */
        }
        const payload = detail && detail.error ? detail.error : detail ?? {};
        const code = payload.code || `http_${r.status}`;
        const message =
          payload.message || `Request failed with status ${r.status}.`;
        throw Object.assign(new Error(message), { code, status: r.status });
      })
      .finally(() => {
        clearTimeout(timer);
        if (signal) signal.removeEventListener("abort", onAbort);
      })
  );
}

export function qs(params) {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v) sp.set(k, String(v));
  }
  const s = sp.toString();
  return s ? `?${s}` : "";
}

export const api = {
  cells: () => request("/api/v1/cells"),
  modelInfo: () => request("/api/v1/model-info"),
  forecast: (cellId, date) =>
    request(`/api/v1/cells/${cellId}/forecast${qs({ date })}`),
  explain: (cellId, date) =>
    request(`/api/v1/cells/${cellId}/explain${qs({ date })}`),
  explanation: (cellId, date, lang) =>
    request(`/api/v1/cells/${cellId}/explanation${qs({ date, lang })}`),
  advisory: (cellId, date) =>
    request(`/api/v1/cells/${cellId}/advisory${qs({ date })}`),
};