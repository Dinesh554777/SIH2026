const KINDS = {
  backend_unavailable: {
    title: "Backend unavailable",
    hint: "The API server is not reachable. Start it (python -m uvicorn src.serving.api:app --port 8000) and retry.",
  },
  timeout: {
    title: "Request timed out",
    hint: "The backend took too long to respond. Retry, or check the API server.",
  },
  unknown_cell: {
    title: "Invalid grid cell",
    hint: "The selected pilot grid cell is not in the catalog.",
  },
  http_404: {
    title: "No forecast available",
    hint: "There is no forecast for this cell and date combination.",
  },
  http_422: {
    title: "Invalid request",
    hint: "The request was rejected by the backend. Check the cell and date.",
  },
  default: {
    title: "Something went wrong",
    hint: "The request could not be completed.",
  },
};

export default function ErrorPanel({ error, onRetry }) {
  const kind = KINDS[error?.code] ?? KINDS.default;
  return (
    <section className="error-panel" data-testid="error-panel" role="alert">
      <div className="error-icon" aria-hidden="true">
        !
      </div>
      <div>
        <h2>{kind.title}</h2>
        <p>{kind.hint}</p>
        {error?.message && error.message !== kind.hint && (
          <p className="muted">Detail: {error.message}</p>
        )}
      </div>
      {onRetry && (
        <button className="btn" onClick={onRetry}>
          Retry
        </button>
      )}
    </section>
  );
}