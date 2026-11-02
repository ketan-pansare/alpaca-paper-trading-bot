"""Replay the strategy over daily closes and compare it with buy-and-hold.

Simplifications, on purpose: trades fill at the day's close, no commissions
or slippage, whole shares only, and each symbol gets an equal slice of cash.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass

from .strategy import LONG, target_position


@dataclass
class Result:
    symbol: str
    days: int
    trades: int
    strategy_return: float
    buy_hold_return: float
    max_drawdown: float
    time_in_market: float


def load_csv(path: str) -> dict[str, list[float]]:
    """Read a CSV with columns date,symbol,close (oldest rows first)."""
    series: dict[str, list[float]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            series.setdefault(row["symbol"].upper(), []).append(float(row["close"]))
    return series


def run_symbol(symbol: str, closes: list[float], fast: int, slow: int, cash: float = 10_000.0) -> Result:
    if len(closes) <= slow:
        raise ValueError(f"{symbol}: need more than {slow} closes, got {len(closes)}")
    shares = 0
    trades = 0
    in_market_days = 0
    peak = cash
    max_dd = 0.0
    start_cash = cash
    for i in range(slow, len(closes)):
        price = closes[i]
        sig = target_position(symbol, closes[: i + 1], fast, slow)
        if sig.target == LONG and shares == 0:
            shares = int(cash // price)
            if shares:
                cash -= shares * price
                trades += 1
        elif sig.target != LONG and shares > 0:
            cash += shares * price
            shares = 0
            trades += 1
        if shares:
            in_market_days += 1
        value = cash + shares * price
        peak = max(peak, value)
        max_dd = max(max_dd, (peak - value) / peak)
    final = cash + shares * closes[-1]
    days = len(closes) - slow
    return Result(
        symbol=symbol,
        days=days,
        trades=trades,
        strategy_return=final / start_cash - 1,
        buy_hold_return=closes[-1] / closes[slow] - 1,
        max_drawdown=max_dd,
        time_in_market=in_market_days / days if days else 0.0,
    )


def format_results(results: list[Result]) -> str:
    head = f"{'Symbol':<14}{'Days':>6}{'Trades':>8}{'Strategy':>11}{'Buy&Hold':>11}{'Max DD':>9}{'In mkt':>9}"
    lines = [head, "-" * len(head)]
    for r in results:
        lines.append(
            f"{r.symbol:<14}{r.days:>6}{r.trades:>8}{r.strategy_return:>10.1%}{r.buy_hold_return:>11.1%}"
            f"{r.max_drawdown:>9.1%}{r.time_in_market:>9.0%}"
        )
    return "\n".join(lines)
