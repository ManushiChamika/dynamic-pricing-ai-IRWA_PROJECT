# core/models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class UserRequest:
    """User request message for pricing optimization."""
    user_id: str
    message: str
    product_name: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class PriceResponse:
    """Response from pricing optimizer agent."""
    user_id: str
    request_message: str
    response_message: str
    product_name: str
    price: Optional[float] = None
    algorithm: Optional[str] = None
    status: str = "success"
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class MarketTick:
    """Market data tick event."""
    sku: str
    our_price: float
    competitor_price: Optional[float] = None
    demand_index: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class PriceProposal:
    """Price proposal from pricing agent."""
    sku: str
    proposed_price: float
    current_price: float
    margin: float
    algorithm: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class AlertEvent:
    """Alert event from alert notifier."""
    sku: str
    kind: str
    message: str
    severity: str  # "info", "warn", "crit"
    ts: datetime = None
    
    def __post_init__(self):
        if self.ts is None:
            self.ts = datetime.utcnow()
