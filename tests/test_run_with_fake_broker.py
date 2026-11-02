"""Exercise `python -m bot run` end to end against a fake broker (no network)."""

import csv

import pytest

import bot.broker
from bot.__main__ import main


class FakeBroker:
    placed = []

    def __init__(self, api_key, secret_key):
        pass

    def account(self):
        return {"equity": 100_000.0, "buying_power": 100_000.0, "trading_blocked": False}

    def market_open(self):
        return True

    def positions(self):
        return {"DOWN": 12}

    def daily_closes(self, symbols, days):
        return {"UP": [100.0 + i for i in range(80)], "DOWN": [200.0 - i for i in range(80)]}

    def submit(self, order):
        FakeBroker.placed.append((order.side, order.qty, order.symbol))
        return f"fake-{len(FakeBroker.placed)}"


@pytest.fixture(autouse=True)
def setup(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ALPACA_API_KEY", "test")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "test")
    monkeypatch.setenv("ALPACA_PAPER", "true")
    monkeypatch.setenv("SYMBOLS", "UP,DOWN")
    monkeypatch.setattr(bot.broker, "AlpacaPaperBroker", FakeBroker)
    FakeBroker.placed = []


def test_dry_run_places_nothing_but_logs(capsys):
    assert main(["run"]) == 0
    out = capsys.readouterr().out
    assert "Would buy" in out and "Would sell 12 DOWN" in out
    assert FakeBroker.placed == []
    rows = list(csv.DictReader(open("journal.csv")))
    assert {r["mode"] for r in rows} == {"dry-run"}


def test_place_orders_sends_paper_orders():
    assert main(["run", "--place-orders"]) == 0
    sides = sorted(p[0] for p in FakeBroker.placed)
    assert sides == ["buy", "sell"]


def test_kill_switch_blocks_everything(capsys, tmp_path):
    (tmp_path / "STOP").write_text("")
    assert main(["run", "--place-orders"]) == 0
    assert FakeBroker.placed == []
    assert "Kill switch" in capsys.readouterr().out
