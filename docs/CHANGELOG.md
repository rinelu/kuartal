# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial SQLite storage layer for watchlist and last-seen report persistence.
- Initial Sectors API client with:
  - authenticated requests
  - request timeouts
  - retry handling with exponential backoff
  - quarterly report date retrieval
  - quarterly financial data retrieval
  - sector growth rankings
  - company report retrieval
  - response normalization
  - short-TTL in-memory caching
  - contract tests for required endpoint fields
- Initial deterministic pipeline computation logic for:
  - year-over-year growth
  - trailing quarterly growth averages
  - sector-relative percentile ranking
  - trend direction classification
- Initial dashboard API layer with Pydantic response schemas.
- Initial mock API data for dashboard development, including:
  - populated watchlist
  - stale/seen report state
  - empty watchlist state
  - pipeline status data
- Initial dashboard frontend with Vite and React, including:
  - watchlist rail
  - ticker tape
  - verdict hero
  - financial table
  - own-trend chart
  - sector percentile scale
  - pipeline status strip
  - delivery status component
- Initial dashboard API client and application entry points.
- Initial dashboard design tokens and Vite configuration.
- Initial dashboard specification and project TODO documentation.
- Initial tests for deterministic calculations and Sectors API integration.
- End-to-end pipeline orchestration for:
  - quarterly report detection
  - financial data computation
  - LLM verdict generation
  - Telegram delivery
  - verdict persistence
  - CompanyCard result generation
- LLM provider resilience and safety handling, including:
  - primary and fallback LLM provider configuration
  - rate-limit error handling
  - retry handling for failed verdict generation
  - deterministic fallback verdict generation
  - advice-language filtering
  - verdict sentence-count validation
  - automatic disclaimer application
- Per-stage pipeline configuration for enabling or disabling LLM generation and delivery.
- Basic scheduler restart backoff configuration.
- Multi-user watchlist support with per-user ticker ownership.
- Per-ticker user routing for delivery.
- Verdict history persistence with:
  - unique ticker/quarter records
  - delivery timestamps
  - opened state
  - time-to-verdict tracking
  - latest and recent verdict retrieval
  - verdict opened-state updates
- UTC timestamp handling for persisted watchlist and verdict data.
- Telegram delivery service with:
  - Telegram Bot API message delivery
  - configurable request timeout and retries
  - exponential backoff for transient failures
  - per-user watchlist delivery routing
  - delivery result tracking
- Watchlist polling scheduler with:
  - recurring pipeline execution
  - configured polling intervals
  - scheduler restart backoff
  - cycle-level error isolation and logging
- Centralized application bootstrap for initializing:
  - primary Gemini LLM provider
  - OpenAI-compatible fallback LLM provider
  - Telegram bot
  - feature-gated pipeline services
- Unified `kuartal` CLI with commands for:
  - API and scheduler serving
  - manual pipeline execution
  - watchlist management
  - Telegram chat ID management
  - delivery retry operations
  - backtest command placeholders
- Gemini REST LLM provider with retry and backoff handling.
- OpenAI-compatible fallback LLM provider for services such as OpenRouter and Groq.
- In-memory pipeline stage status tracking and pipeline status API endpoint.
- Watchlist CRUD API endpoints.
- Verdict opened-state API endpoint.
- Persistent Telegram chat ID storage for per-user delivery.
- Pending delivery lookup and redelivery support.
- Daily price API endpoint and normalization for backtest inputs.

### Changed

- Centralized environment and configuration loading to provide a single configuration interface across the application.
- Extended application configuration with:
  - fallback LLM provider settings
  - pipeline stage controls
  - Telegram delivery settings
  - scheduler configuration
- Extended the Sectors API financial endpoint typing to return normalized `QuarterFinancial` records.
- Extended SQLite watchlist storage to support multiple users per ticker.
- Updated report persistence to support per-ticker quarterly processing and idempotent verdict logging.
- Updated LLM prompts to produce 2–3 short, factual, neutral sentences without investment advice or recommendations.
- Added a deterministic verdict fallback so pipeline execution can continue without a usable LLM response.
- Updated pipeline execution so failures for individual tickers are isolated and do not stop the remaining watchlist from processing.
- Added explicit pipeline stage error reporting for trigger, compute, verdict, delivery, and persistence failures.
- Added scheduled watchlist polling to continuously process configured tickers.
- Added retry and failure handling to Telegram message delivery so transient Telegram API failures do not immediately terminate delivery.
- Extended LLM provider handling to support primary/fallback failover with shared error and retry behavior.
- Added persisted per-user Telegram chat IDs to support targeted multi-user delivery.
- Added delivery retry handling based on persisted delivery state.
- Added pipeline status reporting so individual stage progress and failures can be observed through the dashboard API.
- Added a unified CLI entry point through the `kuartal` project script.
- Extended financial normalization to handle alternate response fields and improved quarter typing.

### Testing

- Added LLM output validation for:
  - prohibited investment-advice language
  - sentence-count limits
  - combined verdict safety checks
- Added retry and fallback handling for LLM provider failures and rate limits.
- Added pipeline failure isolation so one ticker failure does not terminate a watchlist run.
- Added idempotent verdict persistence for the same ticker and quarter.
- Extended storage behavior to cover multi-user watchlists and verdict history.
- Preserved existing deterministic calculation tests and Sectors API integration tests.
- Added coverage for Telegram delivery retry and failure handling.
- Added scheduler execution and restart behavior coverage.
- Added bootstrap configuration and provider initialization tests.
- Added CLI command and entry-point coverage.
- Added Gemini and OpenAI-compatible provider tests.
- Added pipeline stage status and API coverage.
- Added watchlist CRUD and verdict opened-state API coverage.
- Added Telegram chat ID persistence and per-user routing coverage.
- Added pending delivery and redelivery coverage.
- Added financial normalization and alternate-field handling tests.
- Added sector contract coverage and expanded pipeline integration tests.
