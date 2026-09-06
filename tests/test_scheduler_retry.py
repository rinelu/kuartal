from datetime import datetime, timezone

from kuartal.scheduler import retry_pending_deliveries
from kuartal.storage.db import Database
from kuartal.storage.models import VerdictLogEntry


def _seed_failed_verdict(db: Database, ticker: str = "BBRI", quarter: str = "Q2'25") -> None:
    db.add_ticker(ticker, "Banks")
    db.add_verdict(VerdictLogEntry(
        ticker=ticker, quarter=quarter, verdict="Revenue grew this quarter.",
        direction="above", percentile=70, delivered_at=None,
        delivery_status="failed",
    ))


class _StubResult:
    def __init__(self, status):
        self.status = status


class _StubBotSucceeds:
    def send_to_watchers(self, db, ticker, text, chat_ids=None):
        return [_StubResult("sent")]


class _StubBotFails:
    def send_to_watchers(self, db, ticker, text, chat_ids=None):
        return [_StubResult("failed")]


def test_retry_pending_deliveries_marks_success(tmp_path):
    db = Database(path=str(tmp_path / "test.db"))
    _seed_failed_verdict(db)

    succeeded = retry_pending_deliveries(db, _StubBotSucceeds())

    assert succeeded == 1
    entry = db.get_verdict("BBRI", "Q2'25")

    assert entry is not None
    assert entry.delivery_status == "sent"
    assert entry.delivered_at is not None

def test_retry_pending_deliveries_leaves_status_failed_on_repeated_failure(tmp_path):
    db = Database(path=str(tmp_path / "test.db"))
    _seed_failed_verdict(db)

    succeeded = retry_pending_deliveries(db, _StubBotFails())

    assert succeeded == 0
    entry = db.get_verdict("BBRI", "Q2'25")

    assert entry is not None
    assert entry.delivery_status == "failed"


def test_retry_pending_deliveries_ignores_already_sent_verdicts(tmp_path):
    db = Database(path=str(tmp_path / "test.db"))
    db.add_ticker("BBCA", "Banks")
    db.add_verdict(VerdictLogEntry(
        ticker="BBCA", quarter="Q2'25", verdict="ok", direction="inline",
        percentile=50, delivered_at=datetime.now(timezone.utc), delivery_status="sent",
    ))

    succeeded = retry_pending_deliveries(db, _StubBotFails())

    assert succeeded == 0  # nothing pending, so the stub is never even asked


def test_retry_pending_deliveries_returns_zero_when_no_telegram_bot(tmp_path):
    db = Database(path=str(tmp_path / "test.db"))
    _seed_failed_verdict(db)

    assert retry_pending_deliveries(db, None) == 0
