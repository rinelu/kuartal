/**
 * Watchlist rail - dashboard.md §2. Ticker, sector, sparkline, "new" badge.
 * Placeholder only: renders the raw fields so the shape is obvious.
 * TODO(dashboard owner): real layout, sparkline (ownTrend), design tokens.
 *
 * @param {object[]} companies - CompanyCard[] (see kuartal/api/schemas.py)
 * @param {string} selected - currently selected ticker
 * @param {(ticker: string) => void} onSelect
 */
export default function WatchlistRail({ companies, selected, onSelect }) {
  return (
    <aside className="kt-hairline">
      {companies.map((c) => (
        <button
          key={c.ticker}
          onClick={() => onSelect(c.ticker)}
          style={{ fontWeight: c.ticker === selected ? 600 : 400 }}
        >
          <span className="kt-mono">{c.ticker}</span> · {c.sector}
          {c.status === "new" && <span className="kt-accent"> new</span>}
        </button>
      ))}
    </aside>
  );
}
