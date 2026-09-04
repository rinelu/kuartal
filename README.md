# Kuartal

**Sector-relative quarterly financial intelligence**

Kuartal turns quarterly financial reports into a simple comparison: **how is a company performing against its own recent history, and how does it compare with its sector?**

It combines deterministic financial analysis with a narrow LLM layer for generating concise, descriptive verdicts.

## What It Does

* **Own-trend analysis** - compares current growth with the trailing four-quarter average.
* **Sector percentile** - ranks a company's growth against its sector peers.
* **Quarter detection** - automatically detects new quarterly reports.
* **LLM verdicts** - converts computed results into short, readable descriptions.
* **Telegram delivery** - sends generated verdicts through Telegram.
* **Web dashboard** - provides a visual interface for monitoring companies and results.
* **Offline backtesting** - evaluates the methodology against historical data.

## Running

> TODO

## Philosophy

**Deterministic analysis first. LLM second.**

Kuartal is designed so that financial calculations remain transparent, reproducible, and testable. The LLM is only responsible for communicating the already-computed result.

There is intentionally **no brokerage integration, trade execution, or order placement** anywhere in the project.

> **Kuartal provides descriptive financial information, not investment advice.**
