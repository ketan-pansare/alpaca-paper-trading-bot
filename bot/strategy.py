"""Trend-following signal: hold a stock while its fast moving average is above its slow one.

Pure functions only, so the logic is easy to test and to read.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

LONG = "long"
FLAT = "flat"


def sma(values: Sequence[float], window: int) -> float | None:
    """Simple moving average of the last `window` values, or None if there isn't enough data."""
    if window <= 0:
        raise ValueError("window must be positive")
    if len(values) < window:
        return None
    tail = values[-window:]
    return sum(tail) / window


@dataclass(frozen=True)
class Signal:
    symbol: str
    target: str  # LONG or FLAT
    fast: float | None
    slow: float | None
    reason: str


def target_position(symbol: str, closes: Sequence[float], fast_window: int, slow_window: int) -> Signal:
    """Decide whether we want to hold `symbol` based on its closing prices (oldest first)."""
    fast = sma(closes, fast_window)
    slow = sma(closes, slow_window)
    if fast is None or slow is None:
        return Signal(symbol, FLAT, fast, slow, f"not enough history ({len(closes)} bars, need {slow_window})")
    if fast > slow:
        return Signal(symbol, LONG, fast, slow, f"uptrend: {fast_window}-day avg {fast:.2f} above {slow_window}-day avg {slow:.2f}")
    return Signal(symbol, FLAT, fast, slow, f"no uptrend: {fast_window}-day avg {fast:.2f} at or below {slow_window}-day avg {slow:.2f}")
