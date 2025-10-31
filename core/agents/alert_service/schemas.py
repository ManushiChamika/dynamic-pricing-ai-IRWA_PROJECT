from pydantic import BaseModel, Field, AwareDatetime, field_validator
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
<<<<<<< HEAD
=======
    hold_for: Optional[str] = None  # "5m"
    severity: Severity = "warn"
    dedupe: str = "sku"
    group_by: List[str] = []
    notify: NotifySpec = NotifySpec()
    enabled: bool = True

    @field_validator("where")
    @classmethod
    def where_or_detector(cls, v, info):
        values = info.data if hasattr(info, 'data') else {}
        if not v and not values.get("detector"):
            raise ValueError("Provide either 'where' or 'detector'.")
        return v

class RuleRecord(BaseModel):
    id: str
    spec: RuleSpec
    version: int

class Alert(BaseModel):
    id: str
    rule_id: str
    sku: str
    title: str
    payload: Dict[str, Any]
    severity: Severity
    ts: AwareDatetime
    fingerprint: str
    owner_id: Optional[str] = None

class Incident(BaseModel):
    id: str
    rule_id: str
    sku: str
    status: IncidentStatus
    first_seen: AwareDatetime
    last_seen: AwareDatetime
    severity: Severity
    title: str
    group_key: str
    owner_id: Optional[str] = None
>>>>>>> 379c70e69f421885ef6145953fb8ca8741ed7a4e
