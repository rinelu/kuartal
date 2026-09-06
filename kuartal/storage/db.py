"""
SQLite storage for the watchlist and last-seen reports.

Uses a single-file database with the standard sqlite3 module
No ORM is needed for the small schema.
"""

from __future__ import annotations
from kuartal.config import settings
from kuartal.storage.models import LastSeenReport, VerdictLogEntry, Watchlist

import sqlite3
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS watchlist (
    ticker TEXT NOT NULL,
    sector TEXT NOT NULL,
    added_at TEXT NOT NULL,
    user TEXT NOT NULL DEFAULT 'default',
    PRIMARY KEY (ticker, user)
);

CREATE TABLE IF NOT EXISTS last_seen_report (
    ticker TEXT PRIMARY KEY,
    period TEXT NOT NULL,
    seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS verdict_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    quarter TEXT NOT NULL,
    verdict TEXT NOT NULL,
    direction TEXT NOT NULL,
    percentile INTEGER NOT NULL,
    delivered_at TEXT,
    opened INTEGER NOT NULL DEFAULT 0,
    time_to_verdict TEXT NOT NULL DEFAULT '',
    delivery_status TEXT NOT NULL DEFAULT 'not_attempted',
    UNIQUE(ticker, quarter)
);

CREATE TABLE IF NOT EXISTS user_chat_ids (
    user TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL
);
"""

class Database:
    def __init__(self, path: str | None = None) -> None:
        self.path  = path or settings.kuartal_db_path
        self._conn = sqlite3.connect(self.path)
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    # --- Watchlist ---

    def add_ticker(self, ticker: str, sector: str, user: str = "default") -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO watchlist (ticker, sector, added_at, user) VALUES (?, ?, ?, ?)",
            (ticker, sector, datetime.now(timezone.utc).isoformat(), user),
        )
        self._conn.commit()

    def remove_ticker(self, ticker: str, user: str = "default") -> None:
        self._conn.execute("DELETE FROM watchlist WHERE ticker = ? AND user = ?", (ticker, user))
        self._conn.commit()

    def list_watchlist(self, user: str | None = None) -> list[Watchlist]:
        if user is None:
            rows = self._conn.execute("SELECT ticker, sector, added_at, user FROM watchlist").fetchall()
        else:
            rows = self._conn.execute(
                "SELECT ticker, sector, added_at, user FROM watchlist WHERE user = ?", (user,)
            ).fetchall()
        return [
            Watchlist(ticker=r[0], sector=r[1], added_at=datetime.fromisoformat(r[2]), user=r[3])
            for r in rows
        ]

    def list_watched_tickers(self) -> list[str]:
        """Distinct tickers across all users - what the scheduler polls."""

        rows = self._conn.execute("SELECT DISTINCT ticker FROM watchlist").fetchall()
        return [r[0] for r in rows]

    def list_users_for_ticker(self, ticker: str) -> list[str]:
        """Users watching `ticker`, for per-user delivery routing."""

        rows = self._conn.execute("SELECT user FROM watchlist WHERE ticker = ?", (ticker,)).fetchall()
        return [r[0] for r in rows]

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

    # --- Verdict log ---

    def add_verdict(self, entry: VerdictLogEntry) -> None:
        """Idempotent per (ticker, quarter): re-running the same quarter
        updates the existing row rather than creating a duplicate"""

        self._conn.execute(
            """INSERT INTO verdict_log 
                    (ticker, quarter, verdict, direction, percentile, delivered_at,
                    opened, time_to_verdict, delivery_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(ticker, quarter) DO UPDATE SET
                   verdict=excluded.verdict,
                   direction=excluded.direction,
                   percentile=excluded.percentile,
                   delivered_at=excluded.delivered_at,
                   opened=excluded.opened,
                   time_to_verdict=excluded.time_to_verdict,
                   delivery_status=excluded.delivery_status""",
            (
                entry.ticker,
                entry.quarter,
                entry.verdict,
                entry.direction,
                entry.percentile,
                entry.delivered_at.isoformat() if entry.delivered_at else None,
                int(entry.opened),
                entry.time_to_verdict,
                entry.delivery_status,
            ),
        )
        self._conn.commit()

    def mark_opened(self, ticker: str, quarter: str) -> None:
        self._conn.execute(
            "UPDATE verdict_log SET opened = 1 WHERE ticker = ? AND quarter = ?", (ticker, quarter)
        )
        self._conn.commit()
    
    def mark_delivery_status(
        self,
        ticker:       str,
        quarter:      str,
        status:       str,
        delivered_at: datetime | None = None
    ) -> None:
        self._conn.execute(
            "UPDATE verdict_log SET delivery_status = ?, delivered_at = ? WHERE ticker = ? AND quarter = ?",
            (status, delivered_at.isoformat() if delivered_at else None, ticker, quarter),
        )
        self._conn.commit()

    def pending_redeliveries(self) -> list[VerdictLogEntry]:
        rows = self._conn.execute(
            """SELECT ticker, quarter, verdict, direction, percentile, delivered_at, opened,
                      time_to_verdict, delivery_status
               FROM verdict_log WHERE delivery_status = 'failed'"""
        ).fetchall()
        return [self._row_to_verdict(r) for r in rows]

    def get_verdict(self, ticker: str, quarter: str) -> VerdictLogEntry | None:
        row = self._conn.execute(
            """SELECT ticker, quarter, verdict, direction, percentile, delivered_at, opened,
                      time_to_verdict, delivery_status
               FROM verdict_log WHERE ticker = ? AND quarter = ?""",
            (ticker, quarter),
        ).fetchone()
        if row is None: return None
        return self._row_to_verdict(row)

    def latest_verdict(self, ticker: str) -> VerdictLogEntry | None:
        row = self._conn.execute(
            """SELECT ticker, quarter, verdict, direction, percentile, delivered_at, opened,
                      time_to_verdict, delivery_status
               FROM verdict_log WHERE ticker = ? ORDER BY id DESC LIMIT 1""",
            (ticker,),
        ).fetchone()
        if row is None: return None
        return self._row_to_verdict(row)

    def recent_verdicts(self, limit: int = 10) -> list[VerdictLogEntry]:
        rows = self._conn.execute(
            """SELECT ticker, quarter, verdict, direction, percentile, delivered_at, opened,
                      time_to_verdict, delivery_status
               FROM verdict_log ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [self._row_to_verdict(r) for r in rows]

    @staticmethod
    def _row_to_verdict(row) -> VerdictLogEntry:
        return VerdictLogEntry(
            ticker=row[0],
            quarter=row[1],
            verdict=row[2],
            direction=row[3],
            percentile=row[4],
            delivered_at=datetime.fromisoformat(row[5]) if row[5] else None,
            opened=bool(row[6]),
            time_to_verdict=row[7],
            delivery_status=row[8],
        )

    # --- Per-user chat id mapping ---

    def set_chat_id(self, user: str, chat_id: str) -> None:
        self._conn.execute(
            """INSERT INTO user_chat_ids (user, chat_id) VALUES (?, ?)
               ON CONFLICT(user) DO UPDATE SET chat_id=excluded.chat_id""",
            (user, chat_id),
        )
        self._conn.commit()

    def get_chat_id(self, user: str) -> str | None:
        row = self._conn.execute("SELECT chat_id FROM user_chat_ids WHERE user = ?", (user,)).fetchone()
        return row[0] if row else None

    def list_chat_ids(self) -> dict[str, str]:
        rows = self._conn.execute("SELECT user, chat_id FROM user_chat_ids").fetchall()
        return { r[0]: r[1] for r in rows }

    def close(self) -> None:
        self._conn.close()
