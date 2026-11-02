"""Guardrails that sit between a signal and an order."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass

from .strategy import FLAT, LONG, Signal


@dataclass(frozen=True)
class Order:
    symbol: str
    side: str  # "buy" or "sell"
    qty: int
    reason: str


def kill_switch_on(path: str) -> bool:
    """Create a file with this name next to the bot to stop it from placing any order."""
    return os.path.exists(path)


def position_size(equity: float, price: float, max_position_pct: float) -> int:
    """Whole shares worth at most `max_position_pct` of equity."""
    if equity <= 0 or price <= 0:
        return 0
    return math.floor(equity * max_position_pct / price)


def plan_orders(
    signals: list[Signal],
    positions: dict[str, int],
    prices: dict[str, float],
    equity: float,
    max_position_pct: float,
    max_orders: int,
) -> tuple[list[Order], list[str]]:
    """Turn target positions into orders, applying sizing and an order cap.

    Returns (orders, skipped) where `skipped` explains anything held back.
    """
    orders: list[Order] = []
    skipped: list[str] = []
    for sig in signals:
        held = positions.get(sig.symbol, 0)
        if sig.target == LONG and held <= 0:
            price = prices.get(sig.symbol, 0.0)
            qty = position_size(equity, price, max_position_pct)
            if qty <= 0:
                skipped.append(f"{sig.symbol}: buy skipped, position size rounds to 0 shares")
                continue
            orders.append(Order(sig.symbol, "buy", qty, sig.reason))
        elif sig.target == FLAT and held > 0:
            orders.append(Order(sig.symbol, "sell", held, sig.reason))
    if len(orders) > max_orders:
        for extra in orders[max_orders:]:
            skipped.append(f"{extra.symbol}: {extra.side} held back, over the {max_orders}-order limit for this run")
        orders = orders[:max_orders]
    return orders, skipped
