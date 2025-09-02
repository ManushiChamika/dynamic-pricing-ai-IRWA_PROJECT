# core/agents/data_collector/connectors/__init__.py
from __future__ import annotations

# --- Optional HTTP JSON connector (only if httpjson.py is present/valid) ---
try:
    from .httpjson import HTTPJSONConnector as _HTTPJSON  # noqa: F401
    from .httpjson import build_connector as _build_httpjson
except Exception:
    _HTTPJSON = None
    _build_httpjson = None

# --- Mock + FakeStore connectors ---
from .mock import mock_ticks
from .fakestore import fakestore_ticks


class MockConnector:
    """
    Async shim around the existing mock generator so it looks like the others.
    Produces normalized tick dicts compatible with DataCollector.ingest_any(...)
    """
    async def ticks(self, sku: str, market: str = "DEFAULT", depth: int = 10):
        for row in mock_ticks(sku=sku, market=market, n=depth):
            yield {
                "sku": row.get("sku") or row.get("sym") or sku,
                "our_price": row.get("our_price") or row.get("price") or row.get("px"),
                "source": row.get("source") or row.get("src") or "mock",
                "market": market,
                "competitor_price": row.get("competitor_price"),
                "demand_index": row.get("demand_index"),
                "ts": row.get("ts"),
            }


def build_connector(kind: str, **kw):
    """
    Factory returning objects that implement: async .ticks(sku, market, depth)
    Supported kinds: 'httpjson' (optional), 'fakestore', 'mock'
    """
    k = (kind or "").lower()

    if k == "httpjson":
        if _build_httpjson is None:
            raise ValueError(
                "httpjson connector not available (missing/invalid httpjson.py)"
            )
        # Delegate to the httpjson builder so its kwargs (base_url, headers, ...) work
        return _build_httpjson("httpjson", **kw)

    if k == "fakestore":
        # Minimal adapter so DataCollector can stream rows from FakeStore
        class _FS:
            async def ticks(self, sku: str, market: str = "DEFAULT", depth: int = 25):
                async for row in fakestore_ticks(sku=sku, market=market, depth=depth):
                    yield row
        return _FS()

    if k == "mock":
        return MockConnector()

    raise ValueError(f"unsupported connector: {kind!r}")
