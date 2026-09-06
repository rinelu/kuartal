"""
Unified command-line entrypoint for Kuartal.

Provides one consistent way to run the API, scheduler, pipeline, watchlist,
delivery retries, and backtest tools, with provider construction handled
centrally by `kuartal.bootstrap`.

Available commands:
    kuartal serve               run the API server + scheduler together
    kuartal serve --api-only    run just the API server
    kuartal run [TICKER]        manual pipeline trigger (replaces demo.trigger_manual)

    kuartal watch add TICKER SECTOR   add a ticker to the watchlist
    kuartal watch remove TICKER       remove a ticker
    kuartal watch list                list the current watchlist

    kuartal watch chat-id set CHAT_ID [--user USER]   set a user's Telegram chat id
    kuartal watch chat-id list                        list all persisted chat ids

    kuartal retry-deliveries    retry verdicts whose delivery previously failed
    kuartal backtest fetch      pull historical data for the backtest
    kuartal backtest analyze    compute the backtest correlation figure

The dashboard remains a separate stack and is not managed by this CLI.
"""

from __future__ import annotations

import argparse
import multiprocessing
import sys

from kuartal.config import settings

def _run_api() -> None:
    import uvicorn
    uvicorn.run("kuartal.api.server:app", host=settings.api_host, port=settings.api_port)

def _run_scheduler() -> None:
    from kuartal.bootstrap import build_all
    from kuartal.scheduler import run_forever
    from kuartal.sectors.client import SectorsClient
    from kuartal.storage.db import Database

    llm_primary, llm_fallback, telegram_bot = build_all()
    run_forever(
        db=Database(),
        sectors_client=SectorsClient(),
        llm_primary=llm_primary,
        llm_fallback=llm_fallback,
        telegram_bot=telegram_bot,
        )

def _cmd_serve(args: argparse.Namespace) -> None:
    print(f"Kuartal API on http://{settings.api_host}:{settings.api_port}  (MOCK_MODE={settings.mock_mode})")
    print("Dashboard is separate - run `npm run dev` in dashboard/ if you need it.")

    if args.api_only:
        _run_api()
        return

    procs = [multiprocessing.Process(target=_run_api), multiprocessing.Process(target=_run_scheduler)]
    for p in procs: p.start()
    try:
        for p in procs: p.join()

    except KeyboardInterrupt:
        for p in procs: p.terminate()

def _cmd_run(args: argparse.Namespace) -> None:
    from kuartal.bootstrap import build_all
    from kuartal.pipeline.run import run_for_ticker
    from kuartal.scheduler import run_cycle
    from kuartal.sectors.client import SectorsClient
    from kuartal.storage.db import Database

    db = Database()
    sectors_client = SectorsClient()
    llm_primary, llm_fallback, telegram_bot = build_all()

    if args.ticker:
        ticker = args.ticker.upper()
        watch = next((w for w in db.list_watchlist() if w.ticker == ticker), None)
        if watch is None:
            print(f"{ticker} is not on the watchlist - run `kuartal watch add {ticker} <SECTOR>` first.")
            sys.exit(1)

        result = run_for_ticker(
            ticker=watch.ticker, sector=watch.sector, db=db, sectors_client=sectors_client,
            llm_primary=llm_primary, llm_fallback=llm_fallback, telegram_bot=telegram_bot, force=True,
        )
        print(f"{result.ticker}: {result.status}")
        if result.card:
            print(result.card["verdict"])
        if result.error:
            print(f"stage={result.error.stage} error={result.error.error}")
        return

    for result in run_cycle(db=db, sectors_client=sectors_client, llm_primary=llm_primary, llm_fallback=llm_fallback, telegram_bot=telegram_bot):
        print(f"{result.ticker}: {result.status}")

def _cmd_watch(args: argparse.Namespace) -> None:
    from kuartal.storage.db import Database

    db = Database()
    if args.watch_action == "add":
        db.add_ticker(args.ticker.upper(), args.sector, user=args.user)
        print(f"Added {args.ticker.upper()} ({args.sector}) for user={args.user}")

    elif args.watch_action == "remove":
        db.remove_ticker(args.ticker.upper(), user=args.user)
        print(f"Removed {args.ticker.upper()} for user={args.user}")

    elif args.watch_action == "list":
        for w in db.list_watchlist():
            print(f"{w.ticker}\t{w.sector}\tuser={w.user}\tadded={w.added_at.isoformat()}")

    elif args.watch_action == "chat-id":
        if args.chat_id_action == "set":
            db.set_chat_id(args.user, args.chat_id)
            print(f"Set chat id for user={args.user}")

        elif args.chat_id_action == "list":
            for user, chat_id in db.list_chat_ids().items():
                print(f"{user}\t{chat_id}")

def _cmd_retry_deliveries(args: argparse.Namespace) -> None:
    from kuartal.bootstrap import build_telegram_bot
    from kuartal.scheduler import retry_pending_deliveries
    from kuartal.storage.db import Database

    db = Database()
    telegram_bot = build_telegram_bot()
    if telegram_bot is None:
        print("pipeline_enable_delivery is false - nothing to retry.")
        return

    succeeded = retry_pending_deliveries(db, telegram_bot)
    print(f"Retried pending deliveries: {succeeded} succeeded.")

def _cmd_backtest(args: argparse.Namespace) -> None:
    print("Backtest is not implemented yet.")
    # if args.backtest_action == "fetch":
    #     from backtest.data_fetch import main as fetch_main
    #     fetch_main()
    # elif args.backtest_action == "analyze":
    #     from backtest.analyze import main as analyze_main
    #     analyze_main()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kuartal")
    sub = parser.add_subparsers(dest="command", required=True)

    p_serve = sub.add_parser("serve", help="run the API server (+ scheduler)")
    p_serve.add_argument("--api-only", action="store_true", help="skip the scheduler, API only")
    p_serve.set_defaults(func=_cmd_serve)

    p_run = sub.add_parser("run", help="manually trigger the pipeline")
    p_run.add_argument("ticker", nargs="?", help="single ticker to force-run; omit to run the full watchlist")
    p_run.set_defaults(func=_cmd_run)

    p_watch = sub.add_parser("watch", help="manage the watchlist")
    watch_sub = p_watch.add_subparsers(dest="watch_action", required=True)
    p_add = watch_sub.add_parser("add")
    p_add.add_argument("ticker")
    p_add.add_argument("sector")
    p_add.add_argument("--user", default="default")
    p_remove = watch_sub.add_parser("remove")
    p_remove.add_argument("ticker")
    p_remove.add_argument("--user", default="default")
    watch_sub.add_parser("list")

    p_chat_id = watch_sub.add_parser("chat-id", help="manage per-user Telegram chat ids")
    chat_id_sub = p_chat_id.add_subparsers(dest="chat_id_action", required=True)
    p_chat_id_set = chat_id_sub.add_parser("set")
    p_chat_id_set.add_argument("--user", default="default")
    p_chat_id_set.add_argument("chat_id")
    chat_id_sub.add_parser("list")

    p_watch.set_defaults(func=_cmd_watch)

    p_retry = sub.add_parser("retry-deliveries", help="retry any verdicts whose delivery previously failed")
    p_retry.set_defaults(func=_cmd_retry_deliveries)

    p_backtest = sub.add_parser("backtest", help="offline backtest engine")
    backtest_sub = p_backtest.add_subparsers(dest="backtest_action", required=True)
    backtest_sub.add_parser("fetch")
    backtest_sub.add_parser("analyze")
    p_backtest.set_defaults(func=_cmd_backtest)

    return parser

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
