from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str
    username: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class LogoutRequest(BaseModel):
    token: str | None = None


class CreateThreadRequest(BaseModel):
    title: Optional[str] = None


class UpdateThreadRequest(BaseModel):
    title: Optional[str] = None


class PostMessageRequest(BaseModel):
    user_name: str
    content: str
    parent_id: Optional[int] = None


class ThreadOut(BaseModel):
    id: int
    title: str
    created_at: str
    updated_at: Optional[str] = None


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    model: Optional[str] = None
    token_in: Optional[int] = None
    token_out: Optional[int] = None
    cost_usd: Optional[str] = None
    api_calls: Optional[int] = None
    agents: Optional[Dict[str, Any]] = None
    tools: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str


class EditMessageRequest(BaseModel):
    content: str
    branch: bool = True


class DeleteMessageResponse(BaseModel):
    ok: bool


class ThreadExport(BaseModel):
    thread: Dict[str, Any]
    messages: List[Dict[str, Any]]


class ThreadImportMessage(BaseModel):
    id: Optional[int] = None
    role: str
    content: str
    model: Optional[str] = None
    token_in: Optional[int] = None
    token_out: Optional[int] = None
    cost_usd: Optional[str] = None
    agents: Optional[Dict[str, Any]] = None
    tools: Optional[Dict[str, Any]] = None
    api_calls: Optional[int] = None
    parent_id: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ThreadImportRequest(BaseModel):
    title: Optional[str] = None
    owner_id: Optional[int] = None
    messages: List[ThreadImportMessage] = []


class UpdateSettingsRequest(BaseModel):
    token: Optional[str] = None
    settings: Dict[str, Any]


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
