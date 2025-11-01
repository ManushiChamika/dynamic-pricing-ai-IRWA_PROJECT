from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.deps import get_current_user, get_repo
from core.agents.data_collector.repo import DataRepo
from core.agents.data_collector.tools import Tools


router = APIRouter(prefix="/api/collector", tags=["collector"])


class StartJobRequest(BaseModel):
    sku: str
    market: Optional[str] = "DEFAULT"
    connector: Optional[str] = "mock"
    depth: Optional[int] = 5


@router.post("/start")
async def start_collection_job(
    req: StartJobRequest,
    current_user: dict = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    tools = Tools(repo)
    result = await tools.start_collection_job(
        sku=req.sku,
        market=req.market or "DEFAULT",
        connector=req.connector or "mock",
        depth=req.depth or 5,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error") or "Failed to start job")
    return result
