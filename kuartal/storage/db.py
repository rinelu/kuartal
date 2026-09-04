"""
SQLite storage for the watchlist and last-seen reports.

Uses a single-file database with the standard sqlite3 module
No ORM is needed for the small schema.
"""

from __future__ import annotations
from kuartal.config import settings
from kuartal.storage.models import LastSeenReport, Watchlist

import sqlite3
from datetime import datetime

SCHEMA = """
CREATE TABLE IF NOT EXISTS watchlist (
    ticker TEXT PRIMARY KEY,
    sector TEXT NOT NULL,
    added_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS last_seen_report (
    ticker TEXT PRIMARY KEY REFERENCES watchlist(ticker),
    period TEXT NOT NULL,
    seen_at TEXT NOT NULL
);
"""

class Database:
    def __init__(self, path: str | None = None) -> None:
        self.path  = path or settings.kuartal_db_path
        self._conn = sqlite3.connect(self.path)
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    # --- Watchlist ---

    def add_ticker(self, ticker: str, sector: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO watchlist (ticker, sector, added_at) VALUES (?, ?, ?)",
            (ticker, sector, datetime.utcnow().isoformat()),
        )
        self._conn.commit()

    def remove_ticker(self, ticker: str) -> None:
        self._conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
        self._conn.commit()

    def list_watchlist(self) -> list[Watchlist]:
        rows = self._conn.execute("SELECT ticker, sector, added_at FROM watchlist").fetchall()
        return [ Watchlist(ticker=r[0], sector=r[1], added_at=datetime.fromisoformat(r[2])) for r in rows ]

    # --- Last seen report ---

    def get_last_seen(self, ticker: str) -> LastSeenReport | None:
        row = self._conn.execute(
            "SELECT ticker, period, seen_at FROM last_seen_report WHERE ticker = ?", (ticker,)
        ).fetchone()

        if row is None: return None
        return LastSeenReport(ticker=row[0], period=row[1], seen_at=datetime.fromisoformat(row[2]))

    def set_last_seen(self, record: LastSeenReport) -> None:
        self._conn.execute(
            """INSERT INTO last_seen_report (ticker, period, seen_at) VALUES (?, ?, ?)
               ON CONFLICT(ticker) DO UPDATE SET period=excluded.period, seen_at=excluded.seen_at""",
            (record.ticker, record.period, record.seen_at.isoformat()),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
