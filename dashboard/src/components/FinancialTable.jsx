/**
 * Quarterly financial table - dashboard.md §2. Revenue, earnings, margin,
 * last 6 quarters.
 * TODO(dashboard owner): real table styling.
 *
 * @param {{q: string, revenue: number, earnings: number}[]} ownTrend
 * @param {number[]} margin
 */
export default function FinancialTable({ ownTrend, margin }) {
  return (
    <table className="kt-hairline kt-mono">
      <thead>
        <tr>
          <th>Quarter</th>
          <th>Revenue</th>
          <th>Earnings</th>
          <th>Margin</th>
        </tr>
      </thead>
      <tbody>
        {ownTrend.map((pt, i) => (
          <tr key={pt.q}>
            <td>{pt.q}</td>
            <td>{pt.revenue}</td>
            <td>{pt.earnings}</td>
            <td>{margin[i] ?? "-"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
