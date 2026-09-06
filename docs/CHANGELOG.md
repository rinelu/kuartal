# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

*No changes yet.*

## [1.0.0] - 2026-09-06

### Initial Release

The first stable release of the project, providing an end-to-end quarterly financial monitoring and verdict pipeline with dashboard visualization and Telegram delivery.

### Added

- **Sectors API client**
  - Authenticated requests with timeouts, retries, and exponential backoff.
  - Quarterly report date and financial data retrieval.
  - Company report retrieval and sector growth rankings.
  - Response normalization and short-TTL in-memory caching.
  - API contract tests for required response fields.
- **Financial analysis**
  - Year-over-year growth calculations.
  - Trailing quarterly growth averages.
  - Sector-relative percentile rankings.
  - Trend direction classification.
  - Daily price API and normalized backtest inputs.
- **Automated pipeline**
  - Quarterly report detection and financial data computation.
  - LLM verdict generation and deterministic fallback verdicts.
  - Telegram delivery and verdict persistence.
  - CompanyCard result generation.
  - Per-ticker failure isolation.
  - Pipeline stage tracking and status reporting.
- **LLM providers**
  - Gemini REST provider with retry and backoff.
  - OpenAI-compatible fallback provider for services such as OpenRouter and Groq.
  - Primary/fallback failover and rate-limit handling.
  - Configurable LLM pipeline stages.
  - Verdict validation for sentence count and prohibited investment-advice language.
  - Automatic disclaimer handling.
- **Watchlists & persistence**
  - SQLite-backed watchlist and report persistence.
  - Multi-user watchlists with per-user ticker ownership.
  - Per-user Telegram chat ID storage and ticker-based delivery routing.
  - Verdict history with ticker/quarter uniqueness, delivery timestamps, opened state, and time-to-verdict tracking.
  - Pending delivery lookup and redelivery support.
- **Telegram**
  - Telegram Bot API integration.
  - Configurable delivery timeouts and retries.
  - Exponential backoff for transient failures.
  - Per-user delivery routing and delivery result tracking.
- **Scheduler**
  - Recurring watchlist polling.
  - Configurable polling intervals.
  - Scheduler restart backoff.
  - Cycle-level error isolation and logging.
- **Dashboard**
  - Vite + React dashboard.
  - Watchlist rail and ticker tape.
  - Verdict hero and financial table.
  - Own-trend chart and sector percentile visualization.
  - Pipeline and delivery status indicators.
  - Dashboard API with Pydantic response schemas.
  - Mock data for populated, empty, stale/seen, and pipeline-status states.
- **API & CLI**
  - Watchlist CRUD API.
  - Verdict opened-state API.
  - Pipeline status API.
  - Unified `kuartal` CLI for serving, manual pipeline execution, watchlist management, Telegram chat IDs, delivery retries, and backtest placeholders.
  - Centralized application bootstrap and environment configuration.

### Testing

- Deterministic financial calculation tests.
- Sectors API integration and contract tests.
- Financial response normalization tests.
- LLM provider, retry, fallback, and safety validation tests.
- Pipeline integration, failure isolation, and idempotent persistence tests.
- Multi-user watchlist and verdict history tests.
- Telegram delivery, routing, retry, and redelivery tests.
- Scheduler execution and restart tests.
- Bootstrap and CLI tests.
- Dashboard API, pipeline status, watchlist CRUD, and verdict state tests.
