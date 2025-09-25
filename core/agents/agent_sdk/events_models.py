from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class MarketTick:
    sku: str
    our_price: float
    competitor_price: Optional[float] = None
    demand_index: float = 0.0
    ts: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PriceProposal:
    sku: str
    proposed_price: float
    current_price: float
    margin: float
    algorithm: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AlertEvent:
    sku: str
    kind: str
    message: str
    severity: str  # info | warn | crit
    ts: datetime = field(default_factory=datetime.utcnow)
