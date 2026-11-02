"""Thin wrapper around alpaca-py, always pinned to the paper environment.

alpaca-py is imported lazily so the backtest and tests run without it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .risk import Order


class AlpacaPaperBroker:
    def __init__(self, api_key: str, secret_key: str):
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.trading.client import TradingClient

        # paper=True is hard-coded: this class can never reach a live account.
        self.trading = TradingClient(api_key, secret_key, paper=True)
        self.data = StockHistoricalDataClient(api_key, secret_key)

    def account(self) -> dict:
        acct = self.trading.get_account()
        return {
            "equity": float(acct.equity),
            "buying_power": float(acct.buying_power),
            "trading_blocked": bool(acct.trading_blocked),
        }

    def market_open(self) -> bool:
        return bool(self.trading.get_clock().is_open)

    def positions(self) -> dict[str, int]:
        return {p.symbol: int(float(p.qty)) for p in self.trading.get_all_positions()}

    def daily_closes(self, symbols: list[str], days: int) -> dict[str, list[float]]:
        from alpaca.data.enums import DataFeed
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        # Calendar days, padded so weekends and holidays still leave enough trading days.
        start = datetime.now(timezone.utc) - timedelta(days=int(days * 1.6) + 10)
        req = StockBarsRequest(symbol_or_symbols=symbols, timeframe=TimeFrame.Day, start=start, feed=DataFeed.IEX)
        bars = self.data.get_stock_bars(req)
        return {sym: [float(b.close) for b in bars.data.get(sym, [])] for sym in symbols}

    def submit(self, order: Order) -> str:
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest

        req = MarketOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            side=OrderSide.BUY if order.side == "buy" else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        placed = self.trading.submit_order(order_data=req)
        return str(placed.id)
