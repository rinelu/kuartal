/**
 * Verdict hero - dashboard.md §2. The LLM's one sentence + disclaimer.
 * `verdict` uses Source Serif 4 per tokens.css (--font-display);
 * everything else stays on --font-ui.
 * TODO(dashboard owner): real hero treatment.
 *
 * @param {string} verdict
 * @param {string} disclaimer
 */
export default function VerdictHero({ verdict, disclaimer }) {
  return (
    <section>
      <p className="kt-display">{verdict}</p>
      <p className="kt-mono" style={{ fontSize: "0.8rem", opacity: 0.7 }}>
        {disclaimer}
      </p>
    </section>
  );
}
