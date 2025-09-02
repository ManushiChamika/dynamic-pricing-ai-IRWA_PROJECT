# core/agents/data_collector/connectors/httpjson.py
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import httpx


class HTTPJSONConnector:
    """
    Simple HTTP→JSON connector that calls a /prices endpoint and yields normalized ticks.

    Expected JSON shape by default:
      { "sku": "<sku>", "prices": [ { "price": <float>, "ts": "<iso>" }, ... ] }

    If your upstream response nests the array (e.g. { "data": [...] }),
    pass price_path=["data"] to drill into that key.
    """

    def __init__(
        self,
        base_url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        source_name: str = "httpjson",
        price_path: Optional[List[str]] = None,
    ) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.headers = headers or {}
        self.source_name = source_name
        self.price_path = price_path or []

    async def fetch_prices(self, sku: str, depth: int = 5) -> List[Dict[str, Any]]:
        if not self.base_url:
            raise ValueError("HTTPJSONConnector requires a non-empty base_url")

        url = f"{self.base_url}/prices?sku={sku}&depth={depth}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=self.headers)
            resp.raise_for_status()
            data = resp.json()

        node: Any = data
        for key in self.price_path:
            # Walk down nested dicts if needed
            if isinstance(node, dict):
                node = node.get(key, {})
            else:
                node = {}

        prices = node if isinstance(node, list) else data.get("prices", [])
        out: List[Dict[str, Any]] = []
        for item in prices:
            try:
                price = float(item["price"])
            except Exception:
                continue
            out.append(
                {
                    "price": price,
                    "ts": item.get("ts"),
                }
            )
        return out

    async def ticks(self, sku: str, market: str = "DEFAULT", depth: int = 5):
        """
        Async generator that yields normalized ticks the DataCollector understands.
        """
        rows = await self.fetch_prices(sku=sku, depth=depth)
        for row in rows:
            yield {
                "sku": sku,
                "our_price": row["price"],
                "source": self.source_name,
                "market": market,
                "competitor_price": None,
                "demand_index": None,
                "ts": row.get("ts"),
            }
            await asyncio.sleep(0)  # cooperative yield


def build_connector(kind: str, **kw) -> HTTPJSONConnector:
    if kind.lower() != "httpjson":
        raise ValueError(f"unsupported connector: {kind}")
    return HTTPJSONConnector(
        base_url=kw.get("base_url", ""),
        headers=kw.get("headers"),
        source_name=kw.get("source_name", "httpjson"),
        price_path=kw.get("price_path"),
    )
