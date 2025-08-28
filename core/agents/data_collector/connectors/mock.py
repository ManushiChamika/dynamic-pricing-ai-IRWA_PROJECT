from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any, Iterable


def mock_ticks(
    sku: str = "SKU-123",
    market: str = "DEFAULT",
    base_price: float = 100.0,
    comp_price: float = 98.0,
    demand: float = 0.5,
    n: int = 5,
) -> Iterable[Dict[str, Any]]:
    for i in range(n):
        yield {
            "sku": sku,
            "market": market,
            "our_price": base_price,
            "competitor_price": comp_price,
            "demand_index": demand,
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "mock",
        }


