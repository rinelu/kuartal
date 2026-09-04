# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
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

### Changed

- Centralized environment and configuration loading to provide a single configuration interface across the application.

### Testing

- Added calculation tests against known financial values without LLM integration.
- Added Sectors API client tests using `respx` to mock HTTP requests and avoid live API calls.
