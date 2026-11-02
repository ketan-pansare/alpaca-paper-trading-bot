import pytest

from bot.strategy import FLAT, LONG, sma, target_position


def test_sma_uses_last_window_values():
    assert sma([1, 2, 3, 4, 5], 2) == 4.5


def test_sma_returns_none_without_enough_data():
    assert sma([1, 2], 3) is None


def test_sma_rejects_bad_window():
    with pytest.raises(ValueError):
        sma([1, 2, 3], 0)


def test_uptrend_targets_long():
    closes = list(range(1, 61))  # steadily rising
    sig = target_position("TEST", closes, 5, 20)
    assert sig.target == LONG
    assert sig.fast > sig.slow


def test_downtrend_targets_flat():
    closes = list(range(60, 0, -1))  # steadily falling
    assert target_position("TEST", closes, 5, 20).target == FLAT


def test_short_history_stays_flat_and_says_why():
    sig = target_position("TEST", [10.0] * 10, 5, 20)
    assert sig.target == FLAT
    assert "not enough history" in sig.reason
