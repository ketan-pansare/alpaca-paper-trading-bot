"""Generate the bundled SYNTHETIC price file used by `python -m bot backtest --sample`.

These are random walks with a seed, not real market prices. They exist so
anyone can try the bot without an account.
"""

import csv
import os
import random
from datetime import date, timedelta

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "sample_prices.csv")
SERIES = {
    # symbol: (start price, daily drift, daily volatility)
    "SAMPLE_TREND": (100.0, 0.0006, 0.012),
    "SAMPLE_CHOP": (50.0, 0.0000, 0.015),
    "SAMPLE_DROP": (80.0, -0.0004, 0.018),
}
DAYS = 520


def main() -> None:
    rng = random.Random(42)
    rows = []
    for sym, (price, drift, vol) in SERIES.items():
        day = date(2024, 1, 2)
        for _ in range(DAYS):
            while day.weekday() >= 5:
                day += timedelta(days=1)
            price *= 1 + drift + rng.gauss(0, vol)
            rows.append({"date": day.isoformat(), "symbol": sym, "close": f"{price:.2f}"})
            day += timedelta(days=1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "symbol", "close"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
