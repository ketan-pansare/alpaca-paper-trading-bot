"""Append every decision to a CSV so each run can be reviewed later."""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone

FIELDS = ["time_utc", "mode", "symbol", "action", "qty", "reason", "order_id"]


def record(path: str, mode: str, symbol: str, action: str, qty: int, reason: str, order_id: str = "") -> None:
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(
            {
                "time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "mode": mode,
                "symbol": symbol,
                "action": action,
                "qty": qty,
                "reason": reason,
                "order_id": order_id,
            }
        )
