from __future__ import annotations

from kuartal import cli
from kuartal.storage.db import Database

def test_build_parser_accepts_every_documented_subcommand():
    parser = cli.build_parser()

    for argv in [
        ["serve"],
        ["serve", "--api-only"],
        ["run"],
        ["run", "BBRI"],
        ["watch", "add", "BBRI", "Banks"],
        ["watch", "remove", "BBRI"],
        ["watch", "list"],
        ["watch", "chat-id", "set", "12345"],
        ["watch", "chat-id", "list"],
        ["retry-deliveries"],
        ["backtest", "fetch"],
        ["backtest", "analyze"],
    ]:
        args = parser.parse_args(argv)
        assert callable(args.func)

def test_watch_add_list_remove_end_to_end(tmp_path, monkeypatch, capsys):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("kuartal.config.settings.kuartal_db_path", db_path)

    parser = cli.build_parser()
    cli._cmd_watch(parser.parse_args(["watch", "add", "bbri", "Banks"]))
    cli._cmd_watch(parser.parse_args(["watch", "list"]))
    out = capsys.readouterr().out
    assert "BBRI" in out
    assert "Banks" in out

    cli._cmd_watch(parser.parse_args(["watch", "remove", "bbri"]))
    db = Database(path=db_path)
    assert db.list_watchlist() == []

def test_watch_chat_id_set_and_list(tmp_path, monkeypatch, capsys):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("kuartal.config.settings.kuartal_db_path", db_path)

    parser = cli.build_parser()
    cli._cmd_watch(parser.parse_args(["watch", "chat-id", "set", "--user", "alice", "999"]))
    cli._cmd_watch(parser.parse_args(["watch", "chat-id", "list"]))

    out = capsys.readouterr().out
    assert "alice" in out
    assert "999" in out

def test_retry_deliveries_noop_when_delivery_disabled(tmp_path, monkeypatch, capsys):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr("kuartal.config.settings.kuartal_db_path", db_path)
    monkeypatch.setattr("kuartal.bootstrap.settings.pipeline_enable_delivery", False)

    parser = cli.build_parser()
    cli._cmd_retry_deliveries(parser.parse_args(["retry-deliveries"]))

    out = capsys.readouterr().out
    assert "nothing to retry" in out
