/**
 * Own-trend chart - dashboard.md §2. Revenue/earnings last 6 quarters,
 * this-quarter growth vs. own 4Q average.
 * TODO(dashboard owner): real chart (recharts is already a dependency).
 *
 * @param {{q: string, revenue: number, earnings: number}[]} ownTrend
 * @param {number} ownAvgGrowth
 * @param {number} thisGrowth
 */
export default function OwnTrendChart({ ownTrend, ownAvgGrowth, thisGrowth }) {
  return (
    <section className="kt-hairline">
      <p>
        This quarter <span className="kt-mono">{(thisGrowth * 100).toFixed(1)}%</span> vs. own 4Q avg{" "}
        <span className="kt-mono">{(ownAvgGrowth * 100).toFixed(1)}%</span>
      </p>
      <ul className="kt-mono">
        {ownTrend.map((pt) => (
          <li key={pt.q}>
            {pt.q}: revenue {pt.revenue}, earnings {pt.earnings}
          </li>
        ))}
      </ul>
    </section>
  );
}
