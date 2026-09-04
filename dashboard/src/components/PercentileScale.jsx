/**
 * Sector percentile scale - dashboard.md §2. Position marker (0-100) + peer count.
 * TODO(dashboard owner): real 0-100 scale visual.
 *
 * @param {number} sectorPercentile
 * @param {number} sectorPeerCount
 * @param {string} sector
 */
export default function PercentileScale({ sectorPercentile, sectorPeerCount, sector }) {
  return (
    <section className="kt-hairline">
      <p className="kt-mono">
        {sectorPercentile}th percentile of {sectorPeerCount} peers in {sector}
      </p>
      {/* naive placeholder bar - replace with the real scale component */}
      <div style={{ background: "var(--hairline)", height: 4, width: "100%" }}>
        <div style={{ background: "var(--accent)", height: 4, width: `${sectorPercentile}%` }} />
      </div>
    </section>
  );
}
