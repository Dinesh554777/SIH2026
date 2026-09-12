export default function Loading({ label = "Loading…" }) {
  return (
    <section className="loading" role="status" data-testid="loading">
      <div className="spinner" aria-hidden="true" />
      <p>{label}</p>
    </section>
  );
}