"""Settings loaded from environment variables (or a local .env file).

The bot is paper-only by design: there is no setting that points it at a
live account. If ALPACA_PAPER is set to anything other than "true", the bot
refuses to start.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


class ConfigError(ValueError):
    """Raised when settings are missing or unsafe."""


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv  # optional dependency
    except ImportError:
        return
    load_dotenv()


def _float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {raw!r}") from exc


def _int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a whole number, got {raw!r}") from exc


@dataclass(frozen=True)
class Settings:
    api_key: str = ""
    secret_key: str = ""
    symbols: list[str] = field(default_factory=lambda: ["SPY", "QQQ", "AAPL"])
    fast_window: int = 20
    slow_window: int = 50
    max_position_pct: float = 0.10
    max_orders_per_run: int = 3
    kill_switch_file: str = "STOP"
    journal_path: str = "journal.csv"

    def validate(self, need_keys: bool) -> None:
        if need_keys and (not self.api_key or not self.secret_key):
            raise ConfigError(
                "Missing API keys. Copy .env.example to .env and add your Alpaca paper keys "
                "(Paper Trading dashboard > API Keys)."
            )
        if self.fast_window <= 0 or self.slow_window <= 0:
            raise ConfigError("FAST_WINDOW and SLOW_WINDOW must be positive.")
        if self.fast_window >= self.slow_window:
            raise ConfigError("FAST_WINDOW must be smaller than SLOW_WINDOW.")
        if not 0 < self.max_position_pct <= 0.5:
            raise ConfigError("MAX_POSITION_PCT must be between 0 and 0.5 (50% of equity).")
        if self.max_orders_per_run < 0:
            raise ConfigError("MAX_ORDERS_PER_RUN cannot be negative.")
        if not self.symbols:
            raise ConfigError("SYMBOLS cannot be empty.")


def load_settings() -> Settings:
    _load_dotenv()
    paper = os.getenv("ALPACA_PAPER", "true").strip().lower()
    if paper != "true":
        raise ConfigError("This bot only trades paper accounts. Set ALPACA_PAPER=true.")
    symbols = [s.strip().upper() for s in os.getenv("SYMBOLS", "SPY,QQQ,AAPL").split(",") if s.strip()]
    return Settings(
        api_key=os.getenv("ALPACA_API_KEY", ""),
        secret_key=os.getenv("ALPACA_SECRET_KEY", ""),
        symbols=symbols,
        fast_window=_int("FAST_WINDOW", 20),
        slow_window=_int("SLOW_WINDOW", 50),
        max_position_pct=_float("MAX_POSITION_PCT", 0.10),
        max_orders_per_run=_int("MAX_ORDERS_PER_RUN", 3),
        kill_switch_file=os.getenv("KILL_SWITCH_FILE", "STOP"),
        journal_path=os.getenv("JOURNAL_PATH", "journal.csv"),
    )
