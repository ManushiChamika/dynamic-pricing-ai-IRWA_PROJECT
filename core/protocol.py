# core/protocol.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class Topic(Enum):
    """
    Event topics used on the in-process bus.
    """
    MARKET_TICK    = "market_tick"
    PRICE_PROPOSAL = "price_proposal"
    PRICE_UPDATE   = "price_update"   # <-- added to satisfy CLI scripts
    ALERT          = "alert"


@dataclass
class MarketTick:
    sku: str
    our_price: float
    competitor_price: Optional[float]
    demand_index: float
    ts: datetime


@dataclass
class PriceProposal:
    sku: str
    proposed_price: float
    margin: float           # e.g. 0.18 for 18%
    ts: datetime


@dataclass
class AlertEvent:
    sku: str
    kind: str               # e.g. "UNDERCUT" | "DEMAND_SPIKE" | "MARGIN_BREACH"
    message: str
    severity: str           # "info" | "warn" | "crit"
    ts: datetime
