from __future__ import annotations

from enum import Enum


class Topic(Enum):
    MARKET_TICK = "market.tick"
    PRICE_PROPOSAL = "price.proposal"
    ALERT = "alert.event"
