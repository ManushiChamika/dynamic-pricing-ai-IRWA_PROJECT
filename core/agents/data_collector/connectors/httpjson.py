# core/agents/data_collector/connectors/httpjson.py
"""
HTTP JSON connector for DataCollector: calls an external HTTP endpoint that
returns JSON with prices and yields normalized ticks for DataCollector.ingest_stream.
"""

import httpx
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Dict, Optional


async def httpjson_ticks(
    sku: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    depth: int = 5,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Expected upstream response shape:
      { "prices": [ {"price": <float>, "ts": "<iso>"} , ... ] }
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(url, headers=headers or {})
        r.raise_for_status()
        payload = r.json()

    prices = payload.get("prices") if isinstance(payload, dict) else []
    if not isinstance(prices, list):
        return

    for row in prices[:depth]:
        try:
            price = float(row.get("price"))
        except Exception:
            continue
        ts = row.get("ts") or datetime.now(timezone.utc).isoformat()
        yield {
            "sku": sku,
            "our_price": price,
            "source": "httpjson",
            "market": "DEFAULT",
            "competitor_price": None,
            "demand_index": None,
            "ts": ts,
        }
