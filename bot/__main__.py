"""Command line entry point.

    python -m bot backtest --sample        # offline, no account needed
    python -m bot backtest                 # real daily bars from Alpaca (needs paper keys)
    python -m bot run                      # dry run: shows the orders it would place
    python -m bot run --place-orders       # places paper orders
"""

from __future__ import annotations

import argparse
import os
import sys

from . import journal
from .backtest import format_results, load_csv, run_symbol
from .config import ConfigError, load_settings
from .risk import kill_switch_on, plan_orders
from .strategy import target_position

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "data", "sample_prices.csv")


def cmd_backtest(args: argparse.Namespace) -> int:
    settings = load_settings()
    settings.validate(need_keys=not args.sample)
    if args.sample:
        series = load_csv(SAMPLE)
        print("Using bundled SYNTHETIC sample prices (not real market data).\n")
    else:
        from .broker import AlpacaPaperBroker

        broker = AlpacaPaperBroker(settings.api_key, settings.secret_key)
        series = broker.daily_closes(settings.symbols, days=args.days)
        print(f"Using Alpaca daily bars (IEX feed) for {', '.join(settings.symbols)}.\n")
    results = []
    for sym, closes in series.items():
        try:
            results.append(run_symbol(sym, closes, settings.fast_window, settings.slow_window))
        except ValueError as exc:
            print(f"Skipped {exc}")
    print(format_results(results))
    print(f"\nRule: hold while the {settings.fast_window}-day average is above the {settings.slow_window}-day average.")
    print("Fills at the close, no costs or slippage. For learning, not investment advice.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    settings = load_settings()
    settings.validate(need_keys=True)
    mode = "paper-order" if args.place_orders else "dry-run"

    if kill_switch_on(settings.kill_switch_file):
        print(f"Kill switch file '{settings.kill_switch_file}' exists. No orders placed.")
        return 0

    from .broker import AlpacaPaperBroker

    broker = AlpacaPaperBroker(settings.api_key, settings.secret_key)
    acct = broker.account()
    if acct["trading_blocked"]:
        print("Your paper account is blocked from trading. Check the Alpaca dashboard.")
        return 1

    closes = broker.daily_closes(settings.symbols, days=settings.slow_window + 5)
    positions = broker.positions()
    prices = {s: c[-1] for s, c in closes.items() if c}
    signals = [target_position(s, closes.get(s, []), settings.fast_window, settings.slow_window) for s in settings.symbols]

    print(f"Paper equity ${acct['equity']:,.2f} · market {'open' if broker.market_open() else 'closed'} · mode {mode}\n")
    for sig in signals:
        print(f"{sig.symbol:<6} target {sig.target:<5} · {sig.reason}")

    orders, skipped = plan_orders(
        signals, positions, prices, acct["equity"], settings.max_position_pct, settings.max_orders_per_run
    )
    for note in skipped:
        print("Held back:", note)
    if not orders:
        print("\nNo orders needed. Positions already match the signals.")
        return 0

    if args.place_orders and not broker.market_open():
        print("\nMarket is closed. Orders would sit until the next open, so none were placed. Run again during market hours.")
        args.place_orders = False
        mode = "dry-run"

    print()
    for order in orders:
        order_id = ""
        if args.place_orders:
            order_id = broker.submit(order)
            print(f"Placed paper {order.side} {order.qty} {order.symbol} · order {order_id}")
        else:
            print(f"Would {order.side} {order.qty} {order.symbol}")
        journal.record(settings.journal_path, mode, order.symbol, order.side, order.qty, order.reason, order_id)
    if not args.place_orders:
        print("\nDry run only. Add --place-orders to send these to your paper account.")
    print(f"Decisions logged to {settings.journal_path}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m bot", description="Paper-only trend-following bot for Alpaca.")
    sub = parser.add_subparsers(dest="command", required=True)

    bt = sub.add_parser("backtest", help="replay the strategy over daily closes")
    bt.add_argument("--sample", action="store_true", help="use bundled synthetic prices; no account needed")
    bt.add_argument("--days", type=int, default=500, help="trading days of history to fetch (default 500)")
    bt.set_defaults(func=cmd_backtest)

    run = sub.add_parser("run", help="check signals and (optionally) place paper orders")
    run.add_argument("--place-orders", action="store_true", help="send orders to your paper account")
    run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as exc:
        print(f"Setup problem: {exc}", file=sys.stderr)
        return 2
    except ImportError:
        print("alpaca-py is not installed. Run: pip install -r requirements.txt", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
