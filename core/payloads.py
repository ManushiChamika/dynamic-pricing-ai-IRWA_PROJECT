from typing import TypedDict

class PriceProposalPayload(TypedDict):
    proposal_id: str
    product_id: str
    previous_price: float
    proposed_price: float

class PriceUpdatePayload(TypedDict):
    proposal_id: str
    product_id: str
    final_price: float
