import pytest

from bot.__main__ import SAMPLE, main
from bot.backtest import load_csv, run_symbol


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    for name in ["ALPACA_API_KEY", "ALPACA_SECRET_KEY", "ALPACA_PAPER"]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)


def test_sample_file_has_three_series():
    series = load_csv(SAMPLE)
    assert set(series) == {"SAMPLE_TREND", "SAMPLE_CHOP", "SAMPLE_DROP"}
    assert all(len(v) > 400 for v in series.values())


def test_backtest_on_rising_prices_trades_and_makes_money():
    closes = [100 + i for i in range(200)]
    r = run_symbol("UP", closes, 5, 20)
    assert r.trades >= 1
    assert r.strategy_return > 0
    assert 0 <= r.max_drawdown < 0.05


def test_backtest_needs_enough_history():
    with pytest.raises(ValueError):
        run_symbol("X", [1.0] * 10, 5, 20)


def test_cli_sample_backtest_runs_without_account(capsys):
    assert main(["backtest", "--sample"]) == 0
    out = capsys.readouterr().out
    assert "SYNTHETIC" in out
    assert "SAMPLE_TREND" in out


def test_cli_run_without_keys_explains_setup(capsys):
    assert main(["run"]) == 2
    assert "Missing API keys" in capsys.readouterr().err
