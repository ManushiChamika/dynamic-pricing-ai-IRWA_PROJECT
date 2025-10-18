from pydantic import BaseModel, Field, AwareDatetime, validator
from typing import Literal, List, Optional, Dict, Any

Severity = Literal["info", "warn", "crit"]
IncidentStatus = Literal["OPEN", "ACKED", "RESOLVED"]

class MarketTick(BaseModel):
    sku: str
    our_price: float
    competitor_price: Optional[float] = None
    demand_index: float = Field(ge=0, le=1)
    ts: AwareDatetime

class PriceProposal(BaseModel):
    sku: str
    proposed_price: float
    margin: float
    ts: AwareDatetime

class NotifySpec(BaseModel):
    channels: List[Literal["ui","slack","email","webhook"]] = ["ui"]
    throttle: Optional[str] = None  # "15m", "1h"
    webhook_url: Optional[str] = None
    email_to: Optional[List[str]] = None

class RuleSpec(BaseModel):
    id: str
    source: Literal["MARKET_TICK","PRICE_PROPOSAL"]
    # either boolean expression or detector
    where: Optional[str] = None
    detector: Optional[str] = None
    field: Optional[str] = None
    params: Dict[str, Any] = {}
    hold_for: Optional[str] = None  # "5m"
    severity: Severity = "warn"
    dedupe: str = "sku"
    group_by: List[str] = []
    notify: NotifySpec = NotifySpec()
    enabled: bool = True

    @validator("where", always=True)
    def where_or_detector(cls, v, values):
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
