from __future__ import annotations

import sqlite3
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .agent_hub import HUB


def _coerce_sequence(value: Optional[Sequence[str]] | Optional[str]) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    out: List[str] = []
    for item in value:
        if not item:
            continue
        candidate = str(item).strip()
        if candidate:
            out.append(candidate)
    return out


# ----------------------------------------------------------------------
# Catalog + Lookup tools
# ----------------------------------------------------------------------
def list_inventory_items(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    return HUB.list_inventory(search=search, limit=int(limit))


def get_inventory_item(sku: str) -> Dict[str, Any]:
    return HUB.get_inventory_item(sku=sku)


def list_pricing_list(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    return HUB.list_pricing(search=search, limit=int(limit))


def list_price_proposals(sku: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    return HUB.list_price_proposals(sku=sku, limit=int(limit))


def list_market_data(search: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
    return HUB.list_market_data(search=search, limit=int(limit))


def list_inventory(search: str = "", limit: int = 10) -> Dict[str, Any]:
    return list_inventory_items(search=search or None, limit=limit)


def list_market_prices(search: str = "", limit: int = 10) -> Dict[str, Any]:
    return list_pricing_list(search=search or None, limit=limit)


def list_proposals(sku: str = "", limit: int = 10) -> Dict[str, Any]:
    return list_price_proposals(sku=sku or None, limit=limit)


# ----------------------------------------------------------------------
# Agent workflows
# ----------------------------------------------------------------------
def register_product(
    *,
    title: str,
    cost: Optional[float] = None,
    sku: Optional[str] = None,
    currency: str = "USD",
    list_price: Optional[float] = None,
    stock: Optional[int] = None,
    competitor_urls: Optional[Sequence[str]] | Optional[str] = None,
    market: str = "DEFAULT",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    urls = _coerce_sequence(competitor_urls)
    return HUB.register_product(
        title=title,
        cost=cost,
        sku=sku,
        currency=currency,
        list_price=list_price,
        stock=stock,
        competitor_urls=urls,
        market=market,
        notes=notes,
    )


def collect_market_data(
    *,
    sku: str,
    competitor_urls: Optional[Sequence[str]] | Optional[str] = None,
    market: str = "DEFAULT",
    depth: int = 3,
) -> Dict[str, Any]:
    urls = _coerce_sequence(competitor_urls)
    return HUB.collect_market_data(
        sku=sku,
        competitor_urls=urls,
        market=market,
        depth=int(depth),
    )


def optimize_price(
    *,
    sku: str,
    user_goal: Optional[str] = None,
    refresh_market: bool = False,
    competitor_urls: Optional[Sequence[str]] | Optional[str] = None,
) -> Dict[str, Any]:
    urls = _coerce_sequence(competitor_urls)
    return HUB.optimize_price(
        sku=sku,
        user_request=user_goal,
        refresh_market=bool(refresh_market),
        competitor_urls=urls,
    )


def run_pricing_workflow(
    *,
    sku: str,
    user_goal: Optional[str] = None,
    refresh_market: bool = False,
    competitor_urls: Optional[Sequence[str]] | Optional[str] = None,
) -> Dict[str, Any]:
    """Backward compatible alias that mirrors optimize_price behaviour."""
    return optimize_price(
        sku=sku,
        user_goal=user_goal,
        refresh_market=refresh_market,
        competitor_urls=competitor_urls,
    )


def run_agent_workflow(
    *,
    title: str,
    cost: Optional[float] = None,
    sku: Optional[str] = None,
    currency: str = "USD",
    list_price: Optional[float] = None,
    stock: Optional[int] = None,
    competitor_urls: Optional[Sequence[str]] | Optional[str] = None,
    market: str = "DEFAULT",
    notes: Optional[str] = None,
    user_intent: Optional[str] = None,
) -> Dict[str, Any]:
    urls = _coerce_sequence(competitor_urls)
    return HUB.run_full_workflow(
        title=title,
        cost=cost,
        sku=sku,
        currency=currency,
        list_price=list_price,
        stock=stock,
        competitor_urls=urls,
        market=market,
        notes=notes,
        user_intent=user_intent,
    )


def scan_for_alerts(
    *,
    sku: Optional[str] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    if sku:
        return HUB.evaluate_alerts(sku=sku)
    return HUB.list_alerts(limit=int(limit))


def request_market_fetch(
    *,
    sku: str,
    competitor_urls: Optional[Sequence[str]] | Optional[str] = None,
    market: str = "DEFAULT",
    depth: int = 3,
) -> Dict[str, Any]:
    return collect_market_data(
        sku=sku,
        competitor_urls=competitor_urls,
        market=market,
        depth=depth,
    )


# ----------------------------------------------------------------------
# Diagnostics (advanced)
# ----------------------------------------------------------------------
def execute_sql(database: str, query: str) -> Dict[str, Any]:
    db_key = (database or "").strip().lower()
    db_path = HUB.app_db if db_key in {"app", "market", "data"} else None
    if not db_path:
        return {"error": f"Unknown database alias '{database}'. Use 'app'."}
    try:
        conn = sqlite3.connect(db_path.as_posix())
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        conn.commit()
    except Exception as exc:
        return {"error": str(exc)}
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return {"ok": True, "rows": [dict(r) for r in rows], "count": len(rows)}


TOOLS_MAP = {
    "register_product": register_product,
    "run_agent_workflow": run_agent_workflow,
    "collect_market_data": collect_market_data,
    "request_market_fetch": request_market_fetch,
    "optimize_price": optimize_price,
    "run_pricing_workflow": run_pricing_workflow,
    "scan_for_alerts": scan_for_alerts,
    "list_inventory_items": list_inventory_items,
    "get_inventory_item": get_inventory_item,
    "list_pricing_list": list_pricing_list,
    "list_price_proposals": list_price_proposals,
    "list_market_data": list_market_data,
    "list_inventory": list_inventory,
    "list_market_prices": list_market_prices,
    "list_proposals": list_proposals,
    "execute_sql": execute_sql,
}
