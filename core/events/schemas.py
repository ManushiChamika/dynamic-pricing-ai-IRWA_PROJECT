from __future__ import annotations
from typing import Dict, Iterable, Mapping

REQUIRED_KEYS: Dict[str, Iterable[str]] = {
    "price.proposal": ("proposal_id", "product_id", "previous_price", "proposed_price"),
    "price.update": ("proposal_id", "product_id", "final_price"),
    "market.fetch.request": ("request_id", "sku", "market", "sources", "horizon_minutes", "depth"),
    "market.fetch.ack": ("request_id", "job_id", "status"),
    "market.fetch.done": ("request_id", "job_id", "status", "tick_count"),
}


def validate_payload(topic: str, payload: Mapping) -> tuple[bool, str | None]:
    try:
        req = REQUIRED_KEYS.get(topic)
        if not req:
            return True, None
        missing = [k for k in req if k not in payload]
        if missing:
            return False, f"missing keys: {','.join(missing)}"
        return True, None
    except Exception as e:
        return False, str(e)
