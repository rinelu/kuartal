# Kuartal TODO

## Sectors API Client (Python)
- [x] Thin authenticated GET wrapper (`sectors/client.py`) - API key header, timeout, retry-with-backoff
- [x] `endpoints.py`: quarterly report dates per ticker
- [x] `endpoints.py`: quarterly financials (revenue, earnings, margin) per ticker
- [x] `endpoints.py`: sector/subsector top-growth rankings (gainers + losers)
- [x] `endpoints.py`: company report (overview/valuation sections) for display context
- [ ] `normalize.py`: ticker formatting, response shape normalization across endpoints - *ticker normalization only (`normalize_ticker`); no generic response-shaping yet*
- [ ] Response caching (in-memory, short TTL) to avoid redundant calls within one pipeline run
- [ ] Graceful degradation when an endpoint rate-limits or errors - pipeline should skip and retry next cycle, never crash - *client retries/raises; no pipeline layer yet to catch and skip*
- [ ] Contract test: confirm each endpoint response actually contains the fields the pipeline assumes - *existing test covers client retry behavior, not response shape*

## Trigger / New-Quarter Detection (Python)
- [ ] Per-ticker "last seen report date" state, compared against Sectors' quarterly date data each cycle - *`last_seen_report` table exists in storage; nothing reads/compares it yet*
- [ ] Polling loop / scheduled check (`scheduler.py`) - interval configurable, not hardcoded - *not started, though `poll_interval_seconds` is already in `config.py`*
- [ ] New-quarter detection fires exactly once per ticker per quarter (idempotent - no duplicate verdicts on re-check)
- [ ] Manual trigger hook for demo purposes (`demo/trigger_manual.py`), reusing the same trigger code path as the real scheduler - no separate fake logic
- [ ] Logging of every check cycle (ticker, checked-at, result) for the "time-to-verdict" metric

## Compute - Own-Trend & Sector Percentile (Python, pure)
- [x] Own-trend growth calculation (this quarter vs. trailing 4-quarter average)
- [x] Sector percentile calculation (this company's growth ranked against live sector peer set from top-growth data)
- [x] Direction classification (`above` / `below` / `inline`) with explicit, documented thresholds - not a magic number buried in a conditional
- [x] Handles missing/partial peer data without crashing (small sectors, newly listed peers)
- [x] Unit tests against hand-computed known values before any LLM step is wired in

## LLM Verdict Generation (Python)
- [x] `llm/base.py` provider interface (single `generate_verdict(payload) -> str` contract)
- [ ] `llm/gemini_provider.py` implementation - *no concrete provider exists yet, only the abstract interface*
- [ ] Fallback provider stub (Groq/OpenRouter) behind the same interface, swappable via config
- [x] `prompt_templates.py`: one narrow, structured prompt template - inputs are the computed deltas/percentile only, never raw statements
- [ ] Output length/format constraint (2–3 sentences, plain language, no jargon) enforced via prompt + a post-generation length check - *prompt asks for one sentence; no code-level check exists*
- [ ] Disclaimer line appended programmatically, not left to the model to include or phrase - **deviation from spec:** the disclaimer is currently baked into the *prompt instruction* ("always end with exactly this sentence"), so compliance depends on the model, not code. Needs to move to a post-generation append.
- [ ] Automated check that verdict text never contains buy/sell/hold/target-price language - reject and regenerate or fall back to a template sentence if it does
- [ ] Retry/backoff on provider rate-limit errors - *no provider implementation to retry yet*

## Delivery (Python, async)
- [ ] Telegram bot integration (`delivery/telegram_bot.py`) - single channel for v1 - *no `delivery/` module exists yet; `telegram_bot_token`/`telegram_chat_id` are in config but unused*
- [ ] Delivery status tracking (sent / failed / opened, where the channel supports read receipts)
- [ ] Retry logic on delivery failure - never silently drop a generated verdict
- [ ] Per-user watchlist → per-user delivery routing

## Storage (Python, SQLite)
- [ ] `storage/models.py`: Watchlist (user, ticker), LastSeenReport (ticker, quarter, date) - *implemented, but `Watchlist` has no `user` field yet - single-user only*
- [x] `storage/db.py`: SQLite access layer
- [ ] Verdict log table (ticker, quarter, verdict text, direction, percentile, delivered-at, opened) - feeds both the dashboard and the metrics - *schema only has `watchlist` and `last_seen_report`; no verdict log table yet*
- [ ] Simple migration path noted for Postgres if usage ever exceeds SQLite's comfort zone (not built now - noted only) - *no note written anywhere yet*

## Orchestration (Python)
- [ ] `pipeline/run.py`: trigger → compute → verdict → deliver, wired end to end - *doesn't exist yet; `compute.py` and `verdict.py` are unwired standalone modules*
- [ ] Structured error handling per stage - one ticker's failure never blocks the rest of the watchlist
- [ ] Config-driven enable/disable per stage (useful for demo runs vs. full runs)
- [ ] Pipeline run produces the exact JSON contract defined in `dashboard.md` §3 - dashboard and backend are built against this shape explicitly - *the contract itself is defined and enforced (`api/schemas.py`); nothing produces it from real data yet*

## Dashboard (React, per `dashboard.md`)
- [ ] Watchlist rail (ticker, sector, sparkline, unread badge) - *component renders raw fields only, explicitly marked placeholder; no sparkline, no design tokens applied*
- [ ] Verdict hero (LLM sentence + disclaimer) - *placeholder styling, not using `--font-display` treatment from tokens.css yet*
- [ ] Own-trend chart (revenue/earnings, last 6 quarters) - *placeholder; recharts is installed but not used in the component yet*
- [ ] Sector percentile scale (position marker + peer count) - *placeholder, no 0–100 visual yet*
- [ ] Quarterly financial table - *placeholder styling*
- [ ] Delivery status panel (channel, last-sent, opened, time-to-verdict) - *placeholder; no failed/retry state*
- [ ] System stats strip (time-to-verdict avg, coverage %, engagement %, backtest correlation) - **not built at all** - `metrics` is already in the API response and schema but `App.jsx` never renders it
- [x] Recent verdicts ticker tape - *wired to real data via `TickerTape`, though visual treatment is still placeholder*
- [ ] Pipeline status strip, wired to real run events (not just the demo simulate button) - *component + mock `/api/pipeline-status` endpoint exist and are wired; but there's no "Simulate incoming report" trigger yet - the whole top bar is a TODO stub in `App.jsx`*
- [ ] Stale/no-new-report state - *mock data includes a stale ticker (BBTN, `status: "seen"`), but the rail doesn't visually distinguish it yet*
- [ ] Pipeline-in-progress state (reuse simulate-button component) - *mock endpoint can return `in_progress`; nothing triggers it yet since there's no simulate button*
- [ ] Delivery-failed state - *no failed scenario in mock data or UI at all*
- [ ] Empty-watchlist / first-run state - *reachable via `?scenario=empty`, renders a bare "Add a ticker" button that doesn't do anything yet*
- [x] `api/client.js`: fetch layer against the Python backend's read endpoints
- [x] Persistent disclaimer bar (non-dismissible)

## Backend API for Dashboard (Python)
- [ ] Minimal read API (`/api/watchlist`, `/api/company/{ticker}`) over `storage/db.py` - thin layer, no new business logic - *works fully in `MOCK_MODE` (default); the live path is a deliberate `501` stub, not yet reading `storage/db.py`*
- [ ] Dev-only endpoint to re-run the pipeline for a selected ticker (backs the dashboard's "Simulate incoming report" button with a real run, not frontend-only fakery) - *`/api/pipeline-status` only polls a fixed mock trace, it doesn't trigger anything*
- [x] CORS/config for local dashboard dev

## Backtest Engine
- [ ] `backtest/data_fetch.py`: pull historical quarterly financials + prices across many tickers/quarters to disk
- [ ] `backtest/native/percentile.c`: rolling percentile computation across the historical panel
- [ ] `backtest/native/Makefile`
- [ ] `backtest/bindings.py`: ctypes/cffi bridge into the compiled C library
- [ ] `backtest/analyze.py`: runs the historical verdict logic quarter-by-quarter, correlates verdict direction against subsequent price behavior
- [ ] Output: the backtest-correlation number shown on the dashboard's system stats strip - kept strictly descriptive, never fed back into live verdict generation - *`backtestCorrelation` is already a mocked field in `api/mock_data.py`, waiting on this section*
- [ ] `backtest/README.md` explicitly states this is a dev-time validation tool, not part of the live/demo pipeline

## Testing & QA
- [x] Unit tests: compute logic (own-trend delta, percentile ranking)
- [ ] Unit tests: Sectors client response normalization - *client HTTP/retry behavior is tested; `normalize.py`'s `normalize_ticker` has no tests yet*
- [ ] Unit tests: advice-language filter on LLM output - *no filter exists yet to test*
- [ ] Integration test: full pipeline run against seeded/mocked Sectors responses, end to end - *no `pipeline/run.py` to test yet*
- [ ] Integration test: dashboard renders correctly against the real backend JSON contract (not just the mock data file) - *no dashboard tests present yet*
- [ ] Manual QA pass: every dashboard state (new, seen, stale, failed, empty) actually reachable, not just designed - *failed state and add-ticker flow aren't reachable yet*

## Deployment & Infra
- [ ] `.env` handling for Sectors API key, LLM API key/provider selection, Telegram bot token - *`config.py`'s `Settings` class fully covers this; `.env.example` itself is currently an empty file - fill it in with the actual key names*
- [ ] Single-command local run (backend + scheduler + dashboard dev server)
- [ ] Basic process supervision for the scheduler loop (restart on crash) - *no scheduler to supervise yet*
- [ ] Deployment target decided (simple VPS/container is enough - no infra complexity needed for this workload)

## Security & Compliance
- [x] No credentials or API keys committed anywhere in the repo - *`.gitignore` correctly excludes `.env` and `*.db`; re-verify before each submission, not a one-time check*
- [ ] Advice-language filter treated as a hard gate, not a soft warning - a verdict that fails it does not get delivered as-is - *no filter exists yet*
- [ ] Rate-limit protection on any exposed API endpoint - *`server.py` has no rate limiting yet*
- [x] Explicit confirmation that no code path ever calls a brokerage/trading API - checked as part of submission review, not assumed - *true today by inspection; re-check this every time new code is added, don't treat it as permanently satisfied*

## Documentation
- [x] `README.md` - what Kuartal is, how to run it
- [x] `dashboard.md` - kept up to date as the source of truth for the frontend contract (already drafted)
- [ ] Setup guide (API keys, running the scheduler, running the dashboard)
- [ ] Competition write-up (problem, why Sectors is indispensable, the dependency test, measurable impact)
- [ ] Demo video script

## Demo & Competition Prep
- [ ] Seeded, reliable demo watchlist (real IDX tickers with a real recent quarter to react to) - *mock data uses BBRI/BBTN, reasonable start, but tied to `MOCK_MODE`, not a live seeded run*
- [ ] Timed end-to-end dry run of the "Simulate incoming report" flow, exactly as it will appear on camera - *the button itself doesn't exist yet, see Dashboard section*
- [ ] Fallback recorded screen capture in case of any live API/network issue during recording
- [ ] Judging-criteria alignment pass: usability (40%), storytelling (30%), technical depth (30%) - checked against the actual submission, not assumed
- [ ] Submission packaging (repo, write-up, video, all consistent with each other)
