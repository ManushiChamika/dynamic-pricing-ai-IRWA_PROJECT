from pydantic import BaseModel, Field, AwareDatetime, validator
from typing import Literal, List, Optional, Dict, Any

# -----------------------------
# Define simple literal types for controlled vocabularies
# -----------------------------

Severity = Literal["info", "warn", "crit"]             # Allowed severity levels
IncidentStatus = Literal["OPEN", "ACKED", "RESOLVED"] # Incident life-cycle states


# -----------------------------
# MARKET DATA MODELS
# -----------------------------

class MarketTick(BaseModel):
    """Represents a single market tick — real-time market event."""
    sku: str                                           # Product identifier
    our_price: float                                   # Our own price
    competitor_price: Optional[float] = None           # Optional competitor price
    demand_index: float = Field(ge=0, le=1)            # Normalized demand index between 0 and 1
    ts: AwareDatetime                                  # Timestamp with timezone awareness


class PriceProposal(BaseModel):
    """Represents a price recommendation or proposal."""
    sku: str                                           # Product identifier
    proposed_price: float                              # Suggested price
    margin: float                                      # Expected margin at proposed price
    ts: AwareDatetime                                  # Timestamp of proposal


# -----------------------------
# NOTIFICATION CONFIGURATION
# -----------------------------

class NotifySpec(BaseModel):
    """Defines how and where alerts should be delivered."""
    channels: List[Literal["ui","slack","email","webhook"]] = ["ui"]  # Delivery channels
    throttle: Optional[str] = None            # Optional throttle duration (e.g., "15m", "1h")
    webhook_url: Optional[str] = None         # For webhook notifications
    email_to: Optional[List[str]] = None      # Email recipients if using email channel


# -----------------------------
# ALERT RULE SPECIFICATION
# -----------------------------

class RuleSpec(BaseModel):
    """Specification for an alert rule."""
    id: str                                               # Rule ID
    source: Literal["MARKET_TICK","PRICE_PROPOSAL"]       # Input type for rule
    # Either a static condition or a detector
    where: Optional[str] = None                           # Boolean expression to evaluate
    detector: Optional[str] = None                        # Optional statistical detector name
    field: Optional[str] = None                           # Data field the detector observes
    params: Dict[str, Any] = {}
