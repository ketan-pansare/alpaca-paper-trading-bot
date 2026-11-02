import pytest

from bot.config import ConfigError, Settings, load_settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    for name in ["ALPACA_API_KEY", "ALPACA_SECRET_KEY", "ALPACA_PAPER", "SYMBOLS", "FAST_WINDOW", "SLOW_WINDOW"]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)  # make sure no real .env is picked up


def test_refuses_anything_but_paper(monkeypatch):
    monkeypatch.setenv("ALPACA_PAPER", "false")
    with pytest.raises(ConfigError, match="only trades paper"):
        load_settings()


def test_defaults_load_without_keys():
    s = load_settings()
    assert s.symbols == ["SPY", "QQQ", "AAPL"]
    s.validate(need_keys=False)


def test_missing_keys_explained_when_needed():
    with pytest.raises(ConfigError, match="Missing API keys"):
        load_settings().validate(need_keys=True)


def test_symbols_are_parsed_and_uppercased(monkeypatch):
    monkeypatch.setenv("SYMBOLS", "msft, nvda ,")
    assert load_settings().symbols == ["MSFT", "NVDA"]


def test_fast_window_must_be_smaller():
    with pytest.raises(ConfigError, match="FAST_WINDOW must be smaller"):
        Settings(fast_window=50, slow_window=20).validate(need_keys=False)


def test_position_cap_is_bounded():
    with pytest.raises(ConfigError, match="MAX_POSITION_PCT"):
        Settings(max_position_pct=0.9).validate(need_keys=False)


def test_non_numeric_window_is_explained(monkeypatch):
    monkeypatch.setenv("FAST_WINDOW", "ten")
    with pytest.raises(ConfigError, match="whole number"):
        load_settings()
