/**
 * Recent verdicts ticker tape - dashboard.md §2. Cross-watchlist feed,
 * most recent first.
 * TODO(dashboard owner): real scrolling/tape treatment.
 *
 * @param {{ticker: string, verdict: string, quarter: string, sentAt: string}[]} recentVerdicts
 */
export default function TickerTape({ recentVerdicts }) {
  return (
    <div className="kt-hairline kt-mono" style={{ display: "flex", gap: "1.5rem", overflowX: "auto" }}>
      {recentVerdicts.map((v, i) => (
        <span key={`${v.ticker}-${i}`}>
          {v.ticker} ({v.quarter}): {v.verdict}
        </span>
      ))}
    </div>
  );
}
