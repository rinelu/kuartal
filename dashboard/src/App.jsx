import { useEffect, useState } from "react";
import { getWatchlist } from "./api/client.js";
import WatchlistRail from "./components/WatchlistRail.jsx";
import VerdictHero from "./components/VerdictHero.jsx";
import OwnTrendChart from "./components/OwnTrendChart.jsx";
import PercentileScale from "./components/PercentileScale.jsx";
import FinancialTable from "./components/FinancialTable.jsx";
import DeliveryStatus from "./components/DeliveryStatus.jsx";
import TickerTape from "./components/TickerTape.jsx";
import PipelineStrip from "./components/PipelineStrip.jsx";

const DISCLAIMER = "Information and analysis only. Not investment advice.";

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [selectedTicker, setSelectedTicker] = useState(null);

  useEffect(() => {
    getWatchlist()
      .then((res) => {
        setData(res);
        if (res.companies.length > 0) {
          setSelectedTicker(res.companies[0].ticker);
        }
      })
      .catch(setError);
  }, []);

  if (error) {
    // TODO(dashboard owner): design an actual error state, this is a placeholder.
    return <div className="kt-hairline">Couldn't reach the API: {error.message}</div>;
  }

  if (!data) {
    // TODO(dashboard owner): loading state.
    return <div>Loading…</div>;
  }

  if (data.companies.length === 0) {
    // Empty watchlist state - dashboard.md §4. First-run add-ticker action,
    // not a blank screen.
    // TODO(dashboard owner): build the actual add-ticker flow.
    return (
      <div>
        <p>No tickers on your watchlist yet.</p>
        <button>Add a ticker</button>
      </div>
    );
  }

  const selected = data.companies.find((c) => c.ticker === selectedTicker) ?? data.companies[0];

  return (
    <div>
      {/* TODO(dashboard owner): Top bar - wordmark, market status, watched
          count, last-checked time, "Simulate incoming report" trigger
          (dashboard.md §2, backed by scheduler.py state - not yet exposed
          via the API; flag to backend owner when you get here). */}

      <div style={{ display: "flex", gap: "1rem" }}>
        <WatchlistRail companies={data.companies} selected={selected.ticker} onSelect={setSelectedTicker} />

        <main>
          <PipelineStrip ticker={selected.ticker} />
          <VerdictHero verdict={selected.verdict} disclaimer={DISCLAIMER} />
          <OwnTrendChart
            ownTrend={selected.ownTrend}
            ownAvgGrowth={selected.ownAvgGrowth}
            thisGrowth={selected.thisGrowth}
          />
          <PercentileScale
            sectorPercentile={selected.sectorPercentile}
            sectorPeerCount={selected.sectorPeerCount}
            sector={selected.sector}
          />
          <FinancialTable ownTrend={selected.ownTrend} margin={selected.margin} />
          <DeliveryStatus
            channel={selected.channel}
            lastSent={selected.lastSent}
            opened={selected.opened}
            timeToVerdict={selected.timeToVerdict}
          />
        </main>
      </div>

      <TickerTape recentVerdicts={data.recentVerdicts} />

      {/* Disclaimer bar - persistent, always visible, not dismissible. */}
      <footer className="kt-hairline kt-mono">{DISCLAIMER}</footer>
    </div>
  );
}
