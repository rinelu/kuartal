# Kuartal TODO

## Sectors API Client (Python)
- [ ] Thin authenticated GET wrapper (`sectors/client.py`) - API key header, timeout, retry-with-backoff
- [ ] `endpoints.py`: quarterly report dates per ticker
- [ ] `endpoints.py`: quarterly financials (revenue, earnings, margin) per ticker
- [ ] `endpoints.py`: sector/subsector top-growth rankings (gainers + losers)
- [ ] `endpoints.py`: company report (overview/valuation sections) for display context
- [ ] `normalize.py`: ticker formatting, response shape normalization across endpoints
- [ ] Response caching (in-memory, short TTL) to avoid redundant calls within one pipeline run
- [ ] Graceful degradation when an endpoint rate-limits or errors - pipeline should skip and retry next cycle, never crash
- [ ] Contract test: confirm each endpoint response actually contains the fields the pipeline assumes

## Trigger / New-Quarter Detection (Python)
- [ ] Per-ticker "last seen report date" state, compared against Sectors' quarterly date data each cycle
- [ ] Polling loop / scheduled check (`scheduler.py`) - interval configurable, not hardcoded
- [ ] New-quarter detection fires exactly once per ticker per quarter (idempotent - no duplicate verdicts on re-check)
- [ ] Manual trigger hook for demo purposes (`demo/trigger_manual.py`), reusing the same trigger code path as the real scheduler - no separate fake logic
- [ ] Logging of every check cycle (ticker, checked-at, result) for the "time-to-verdict" metric

## Compute - Own-Trend & Sector Percentile (Python, pure)
- [ ] Own-trend growth calculation (this quarter vs. trailing 4-quarter average)
- [ ] Sector percentile calculation (this company's growth ranked against live sector peer set from top-growth data)
- [ ] Direction classification (`above` / `below` / `inline`) with explicit, documented thresholds - not a magic number buried in a conditional
- [ ] Handles missing/partial peer data without crashing (small sectors, newly listed peers)
- [ ] Unit tests against hand-computed known values before any LLM step is wired in

## LLM Verdict Generation (Python)
- [ ] `llm/base.py` provider interface (single `generate_verdict(payload) -> str` contract)
- [ ] `llm/gemini_provider.py` implementation
- [ ] Fallback provider stub (Groq/OpenRouter) behind the same interface, swappable via config
- [ ] `prompt_templates.py`: one narrow, structured prompt template - inputs are the computed deltas/percentile only, never raw statements
- [ ] Output length/format constraint (2–3 sentences, plain language, no jargon) enforced via prompt + a post-generation length check
- [ ] Disclaimer line appended programmatically, not left to the model to include or phrase
- [ ] Automated check that verdict text never contains buy/sell/hold/target-price language - reject and regenerate or fall back to a template sentence if it does
- [ ] Retry/backoff on provider rate-limit errors

## Delivery (Python, async)
- [ ] Telegram bot integration (`delivery/telegram_bot.py`) - single channel for v1
- [ ] Delivery status tracking (sent / failed / opened, where the channel supports read receipts)
- [ ] Retry logic on delivery failure - never silently drop a generated verdict
- [ ] Per-user watchlist → per-user delivery routing

## Storage (Python, SQLite)
- [ ] `storage/models.py`: Watchlist (user, ticker), LastSeenReport (ticker, quarter, date)
- [ ] `storage/db.py`: SQLite access layer
- [ ] Verdict log table (ticker, quarter, verdict text, direction, percentile, delivered-at, opened) - feeds both the dashboard and the metrics
- [ ] Simple migration path noted for Postgres if usage ever exceeds SQLite's comfort zone (not built now - noted only)

## Orchestration (Python)
- [ ] `pipeline/run.py`: trigger → compute → verdict → deliver, wired end to end
- [ ] Structured error handling per stage - one ticker's failure never blocks the rest of the watchlist
- [ ] Config-driven enable/disable per stage (useful for demo runs vs. full runs)
- [ ] Pipeline run produces the exact JSON contract defined in `dashboard.md` §3 - dashboard and backend are built against this shape explicitly

## Dashboard (React, per `dashboard.md`)
- [ ] Watchlist rail (ticker, sector, sparkline, unread badge)
- [ ] Verdict hero (LLM sentence + disclaimer)
- [ ] Own-trend chart (revenue/earnings, last 6 quarters)
- [ ] Sector percentile scale (position marker + peer count)
- [ ] Quarterly financial table
- [ ] Delivery status panel (channel, last-sent, opened, time-to-verdict)
- [ ] System stats strip (time-to-verdict avg, coverage %, engagement %, backtest correlation)
- [ ] Recent verdicts ticker tape
- [ ] Pipeline status strip, wired to real run events (not just the demo simulate button)
- [ ] Stale/no-new-report state
- [ ] Pipeline-in-progress state (reuse simulate-button component)
- [ ] Delivery-failed state
- [ ] Empty-watchlist / first-run state
- [ ] `api/client.js`: fetch layer against the Python backend's read endpoints
- [ ] Persistent disclaimer bar (non-dismissible)

## Backend API for Dashboard (Python)
- [ ] Minimal read API (`/api/watchlist`, `/api/company/{ticker}`) over `storage/db.py` - thin layer, no new business logic
- [ ] Dev-only endpoint to re-run the pipeline for a selected ticker (backs the dashboard's "Simulate incoming report" button with a real run, not frontend-only fakery)
- [ ] CORS/config for local dashboard dev

## Backtest Engine
- [ ] `backtest/data_fetch.py`: pull historical quarterly financials + prices across many tickers/quarters to disk
- [ ] `backtest/native/percentile.c`: rolling percentile computation across the historical panel
- [ ] `backtest/native/Makefile`
- [ ] `backtest/bindings.py`: ctypes/cffi bridge into the compiled C library
- [ ] `backtest/analyze.py`: runs the historical verdict logic quarter-by-quarter, correlates verdict direction against subsequent price behavior
- [ ] Output: the backtest-correlation number shown on the dashboard's system stats strip - kept strictly descriptive, never fed back into live verdict generation
- [ ] `backtest/README.md` explicitly states this is a dev-time validation tool, not part of the live/demo pipeline

## Testing & QA
- [ ] Unit tests: compute logic (own-trend delta, percentile ranking)
- [ ] Unit tests: Sectors client response normalization
- [ ] Unit tests: advice-language filter on LLM output
- [ ] Integration test: full pipeline run against seeded/mocked Sectors responses, end to end
- [ ] Integration test: dashboard renders correctly against the real backend JSON contract (not just the mock data file)
- [ ] Manual QA pass: every dashboard state (new, seen, stale, failed, empty) actually reachable, not just designed

## Deployment & Infra
- [ ] `.env` handling for Sectors API key, LLM API key/provider selection, Telegram bot token
- [ ] Single-command local run (backend + scheduler + dashboard dev server)
- [ ] Basic process supervision for the scheduler loop (restart on crash)
- [ ] Deployment target decided (simple VPS/container is enough - no infra complexity needed for this workload)

## Security & Compliance
- [ ] No credentials or API keys committed anywhere in the repo
- [ ] Advice-language filter treated as a hard gate, not a soft warning - a verdict that fails it does not get delivered as-is
- [ ] Rate-limit protection on any exposed API endpoint
- [ ] Explicit confirmation that no code path ever calls a brokerage/trading API - checked as part of submission review, not assumed

## Documentation
- [ ] `README.md` - what Kuartal is, how to run it
- [ ] `Kuartal.md` - kept up to date as the source of truth for scope/architecture (already drafted)
- [ ] `dashboard.md` - kept up to date as the source of truth for the frontend contract (already drafted)
- [ ] Setup guide (API keys, running the scheduler, running the dashboard)
- [ ] Competition write-up (problem, why Sectors is indispensable, the dependency test, measurable impact)
- [ ] Demo video script

## Demo & Competition Prep
- [ ] Seeded, reliable demo watchlist (real IDX tickers with a real recent quarter to react to)
- [ ] Timed end-to-end dry run of the "Simulate incoming report" flow, exactly as it will appear on camera
- [ ] Fallback recorded screen capture in case of any live API/network issue during recording
- [ ] Judging-criteria alignment pass: usability (40%), storytelling (30%), technical depth (30%) - checked against the actual submission, not assumed
- [ ] Submission packaging (repo, write-up, video, all consistent with each other)
