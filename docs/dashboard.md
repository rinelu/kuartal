# Kuartal Dashboard

Web dashboard for Kuartal v1. Single-page view of the watchlist and the
sector-relative verdict for each watched company.

## Purpose

Give the user (and the demo video) one screen that shows: what's being
watched, the pipeline actually running, the verdict itself, and the data
behind the verdict - without requiring the user to leave the page or read
raw financials.

## Layout / sections

| Section | Shows | Backed by |
|---|---|---|
| Top bar | Wordmark, market status, watched count, last-checked time, "Simulate incoming report" trigger | `scheduler.py` state |
| Watchlist rail | Ticker, sector, sparkline, unread ("new") badge | `storage/models.py` Watchlist + LastSeenReport |
| System stats | Avg. time-to-verdict, watchlist coverage %, verdict engagement %, backtest correlation | metrics in Kuartal.md §7 |
| Pipeline status strip | 4-step live trace: report detected → history read → sector ranked → verdict generated | `pipeline/run.py` |
| Verdict hero | The one sentence the LLM produced, plus the disclaimer line | `llm/verdict.py` output |
| Own-trend chart | Revenue/earnings, last 6 quarters, this-quarter growth vs. own 4Q average | `pipeline/compute.py` |
| Sector percentile scale | Position marker (0–100) + peer count | `pipeline/compute.py` (via `top-growth`) |
| Quarterly financial table | Revenue, earnings, margin - last 6 quarters | `sectors/endpoints.py` financials |
| Delivery status | Channel, last-sent time, opened/not opened, time-to-verdict | `delivery/telegram_bot.py` |
| Recent verdicts ticker tape | Cross-watchlist feed, most recent first | aggregated verdict log |
| Disclaimer bar | Persistent, always visible, not dismissible | static |

## Data contract

The dashboard renders from one object per company. This is the exact shape
`pipeline/run.py` must produce and hand to the frontend - build the backend
to satisfy this shape, not the other way around.

```json
{
  "ticker": "BBRI",
  "name": "Bank Rakyat Indonesia",
  "sector": "Banks",
  "quarter": "Q2 2026",
  "status": "new | seen",
  "verdict": "string, LLM-generated, descriptive only",
  "direction": "above | below | inline",
  "ownTrend": [{ "q": "Q1'25", "revenue": 62, "earnings": 24 }],
  "ownAvgGrowth": 0.15,
  "thisGrowth": 0.09,
  "sectorPercentile": 65,
  "sectorPeerCount": 34,
  "margin": [39.5, 39.1, 40.3, 40.9, 41.1, 40.8],
  "channel": "Telegram",
  "lastSent": "ISO timestamp or relative string",
  "opened": true,
  "timeToVerdict": "3m 40s"
}
```

Plus one feed array (`recentVerdicts`) and one metrics object
(`{ timeToVerdictAvg, coverageRate, engagementRate, backtestCorrelation }`).

No field on this dashboard is decorative - every value maps to a real
Sectors-derived computation from the pipeline. If a field can't be populated
from real data, remove it from the dashboard rather than fake it.

## States the dashboard must handle

v1 mock only implements the "happy path." Before wiring to the live
pipeline, add:

- **Stale / no new report** - watched ticker with no report this cycle.
  Show last verdict, greyed status, no "new" badge.
- **Pipeline in progress** - the 4-step strip mid-run (already built for the
  simulate button; reuse the same component for real runs).
- **Delivery failed** - channel send error; show retry state, don't silently
  drop the verdict.
- **Empty watchlist** - first-run state with an add-ticker action, not a
  blank screen.

## Design tokens (for consistency if extended)

- Ink `#161A21`, paper `#EDEFEA`, hairline `#D3D6CB`
- Positive `#1F6F5C`, negative `#B24B28`, brand accent `#B98A2E`
- Display: Source Serif 4 (verdict sentence only) · UI: Inter · Data/numerals: IBM Plex Mono
- Sharp corners, hairline borders, no drop shadows, no gradients
- Motion: reserved for the pipeline-status reveal only - nothing else animates on load

## Backend hookup (when leaving mock data)

- Expose one read endpoint from the Python pipeline (`/api/watchlist`,
  `/api/company/{ticker}`) that returns the exact contract in §3 - a thin
  FastAPI/Flask layer over `storage/db.py`, not new business logic.
- The "Simulate incoming report" button should call a real dev-only endpoint
  that re-runs `pipeline/run.py` against the last stored quarter for the
  selected ticker, rather than being frontend-only fakery, once the backend
  exists - this keeps the demo honest per the rules' "not faked for the
  demo" technical-depth criterion.

## Non-goals

- No portfolio-value tracking, no price ticker beyond what a verdict needs.
- No user-facing settings/config UI in v1 - watchlist editing is enough.
- No mobile-specific layout in v1 - desktop-first, since the judging video
  is a screen recording.
