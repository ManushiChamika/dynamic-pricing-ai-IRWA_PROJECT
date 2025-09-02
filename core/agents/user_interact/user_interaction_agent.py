from __future__ import annotations

import http.client, json, os, re
from typing import Any, Dict, Optional

from core.bus import bus
from core.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL
from core.agents.analytics import insights
from core.agents.intent_parser import parse_intent

USER_REQUEST = "USER_REQUEST"
USER_REPLY   = "USER_REPLY"

MARKET_DB_PATH = os.getenv("MARKET_DB_PATH", "market.db")


def _parse_days(msg: str, default_days: int = 7) -> int:
    m = re.search(r"\b(last|past)\s+(\d{1,3})\s*(day|days|d)\b", msg)
    if m:
        try:
            return max(1, int(m.group(2)))
        except Exception:
            pass
    m2 = re.search(r"\b(\d{1,3})\s*(day|days|d)\b", msg)
    if m2:
        try:
            return max(1, int(m2.group(1)))
        except Exception:
            pass
    return default_days


class UserInteractionAgent:
    def __init__(self, user_name: str):
        self.user_name = user_name
        self.last_result: Optional[dict] = None  # remember last product

    # ---------- context memory ----------
    def _refer_last_product(self, message: str) -> Optional[dict]:
        """If user says 'it/this/that/the product', reuse last_result"""
        if not self.last_result:
            return None
        pronouns = ("it", "that", "this", "the product")
        if any(p in (message or "").lower() for p in pronouns):
            return self.last_result
        return None

    # ---------- intent helpers ----------
    def is_dynamic_pricing_related(self, message: str) -> bool:
        keys = [
            "price", "pricing", "discount", "margin", "demand",
            "competitor", "reprice", "optimize", "update",
            "trend", "trending", "mover", "cheapest", "expensive"
        ]
        return any(k in (message or "").lower() for k in keys)

    # ---------- public entry ----------
    def get_response(self, message: str) -> str:
        if not self.is_dynamic_pricing_related(message):
            return "I can only answer questions related to the dynamic pricing system."

        intent = parse_intent(message)

        # ---- Cheapest ----
        if intent.type == "cheapest":
            row = insights.cheapest_product(MARKET_DB_PATH, days=intent.period)
            if not row:
                return "No product data available."
            self.last_result = {"sku": row["sku"], "label": row["label"]}
            return f"Cheapest product: **{row['label']}** ({row['sku']}) at {row['price']:.2f}"

        # ---- Most Expensive ----
        if intent.type == "most_expensive":
            row = insights.most_expensive_product(MARKET_DB_PATH, days=intent.period)
            if not row:
                return "No product data available."
            self.last_result = {"sku": row["sku"], "label": row["label"]}
            return f"Most expensive product: **{row['label']}** ({row['sku']}) at {row['price']:.2f}"

        # ---- Trending ----
        if intent.type == "trending":
            rows = insights.top_trending_by_volume(
                MARKET_DB_PATH,
                days=intent.period,
                limit=intent.count,
                market="DEFAULT"
            )
            if not rows:
                return "No trending data yet."
            self.last_result = {"sku": rows[0]["sku"], "label": rows[0]["label"]}
            lines = [f"Top {len(rows)} trending products:"]
            for r in rows:
                lines.append(f"- **{r['label']}** ({r['sku']}): {r['n']} updates")
            return "\n".join(lines)

        # ---- Competitor Pressure ----
        if intent.type == "competitor_pressure":
            rows = insights.highest_competitor_pressure(
                MARKET_DB_PATH,
                days=intent.period,
                limit=intent.count,
                market="DEFAULT"
            )
            if not rows:
                return "No competitor data yet."
            self.last_result = {"sku": rows[0]["sku"], "label": rows[0]["label"]}
            lines = ["Competitor pressure:"]
            for r in rows:
                lines.append(
                    f"- **{r['label']}** ({r['sku']}): ours {r['avg_ours']:.2f}, comp {r['avg_comp']:.2f}"
                )
            return "\n".join(lines)

        # ---- Stats ----
        if intent.type == "stats" and intent.product:
            s = insights.stats_for_period(
                MARKET_DB_PATH,
                intent.product,
                days=intent.period,
                market="DEFAULT"
            )
            if not s:
                return f"No data for {intent.product}."
            self.last_result = {"sku": intent.product, "label": s["label"]}
            return (f"Stats for {s['label']} ({intent.product}): "
                    f"avg {s['avg_price']:.2f}, min {s['min_price']:.2f}, "
                    f"max {s['max_price']:.2f}, updates {s['updates']}.")

        # ---- Price of referenced product ----
        ref = self._refer_last_product(message)
        if ref and "price" in message.lower():
            row = insights.latest_price_for(MARKET_DB_PATH, ref["sku"], "DEFAULT")
            if row:
                return f"Latest price of **{ref['label']}** ({ref['sku']}): {row['our_price']:.2f}"
            return f"No recent price for {ref['label']}."

        return "I can only answer questions about pricing, products, trends, or competition."
