from typing import TypedDict, Optional, List

class PriceProposalPayload(TypedDict):
    proposal_id: str
    product_id: str
    previous_price: float
    proposed_price: float

class PriceUpdatePayload(TypedDict):
    proposal_id: str
    product_id: str
    final_price: float

class MarketFetchRequestPayload(TypedDict):
    request_id: str
    sku: str
    market: str
    sources: List[str]
    urls: Optional[List[str]]
    horizon_minutes: int
    depth: int

class MarketFetchAckPayload(TypedDict):
    request_id: str
    job_id: str
    status: str  # "QUEUED" | "RUNNING" | "FAILED"
    error: Optional[str]

class MarketFetchDonePayload(TypedDict):
    request_id: str
    job_id: str
    status: str  # "DONE"
    tick_count: int
