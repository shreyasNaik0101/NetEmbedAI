export default function ShowcaseNotice() {
  return (
    <aside className="showcase-notice" aria-label="Prototype limitations">
      <strong>Experimental local prototype</strong>
      <span>
        Model scores are not probabilities of correctness. Listed services are
        model labels; local reliability varies and has not been established for
        every service.
      </span>
    </aside>
  );
}
