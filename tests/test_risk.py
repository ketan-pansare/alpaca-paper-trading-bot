from bot.risk import kill_switch_on, plan_orders, position_size
from bot.strategy import FLAT, LONG, Signal


def sig(symbol, target):
    return Signal(symbol, target, 1.0, 1.0, "test")


def test_position_size_caps_at_percent_of_equity():
    assert position_size(100_000, 250.0, 0.10) == 40  # $10,000 / $250


def test_position_size_zero_for_bad_inputs():
    assert position_size(0, 100.0, 0.1) == 0
    assert position_size(1000, 0.0, 0.1) == 0


def test_buy_when_long_and_not_held():
    orders, skipped = plan_orders([sig("AAA", LONG)], {}, {"AAA": 100.0}, 10_000, 0.1, 5)
    assert [(o.side, o.qty) for o in orders] == [("buy", 10)]
    assert skipped == []


def test_sell_entire_position_when_flat():
    orders, _ = plan_orders([sig("AAA", FLAT)], {"AAA": 7}, {"AAA": 100.0}, 10_000, 0.1, 5)
    assert [(o.side, o.qty) for o in orders] == [("sell", 7)]


def test_no_order_when_already_matching():
    orders, _ = plan_orders([sig("AAA", LONG), sig("BBB", FLAT)], {"AAA": 3}, {"AAA": 1.0, "BBB": 1.0}, 1000, 0.1, 5)
    assert orders == []


def test_skips_buy_that_rounds_to_zero_shares():
    orders, skipped = plan_orders([sig("BIG", LONG)], {}, {"BIG": 5000.0}, 10_000, 0.1, 5)
    assert orders == []
    assert "rounds to 0" in skipped[0]


def test_order_cap_holds_back_extras():
    signals = [sig(s, LONG) for s in ["A", "B", "C"]]
    orders, skipped = plan_orders(signals, {}, {"A": 1.0, "B": 1.0, "C": 1.0}, 1000, 0.1, 2)
    assert [o.symbol for o in orders] == ["A", "B"]
    assert "over the 2-order limit" in skipped[0]


def test_kill_switch(tmp_path):
    flag = tmp_path / "STOP"
    assert not kill_switch_on(str(flag))
    flag.write_text("")
    assert kill_switch_on(str(flag))
