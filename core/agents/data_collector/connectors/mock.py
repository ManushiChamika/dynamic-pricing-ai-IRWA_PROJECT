# core/agents/data_collector/connectors/mock.py
from datetime import datetime, timezone
from typing import Iterable, Dict, Any

def mock_ticks(sku: str = "SKU-123", market: str = "LK", n: int = 5) -> Iterable[Dict[str, Any]]:
    for i in range(n):
        yield {
            "sku": sku,
            "market": market,
            "our_price": 100.0 + float(i),
            "competitor_price": 98.0 + float(i),
            "demand_index": 0.45 + i * 0.05,
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "mock",
        }
