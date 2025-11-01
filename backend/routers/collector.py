from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
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


@router.get("/active")
async def get_active_jobs(
    current_user: dict = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    tools = Tools(repo)
    return await tools.get_active_jobs()


@router.get("/recent")
async def get_recent_jobs(
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    tools = Tools(repo)
    return await tools.get_recent_jobs(limit=limit)


@router.get("/freshness")
async def check_freshness(
    sku: str = Query(...),
    market: str = Query("DEFAULT"),
    current_user: dict = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    tools = Tools(repo)
    return await tools.check_data_freshness(sku=sku, market=market)


@router.get("/products")
async def list_products(
    current_user: dict = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    tools = Tools(repo)
    return await tools.get_all_products()


@router.get("/stale")
async def list_stale_products(
    threshold_minutes: int = Query(60, ge=1, le=10080),
    current_user: dict = Depends(get_current_user),
    repo: DataRepo = Depends(get_repo),
):
    tools = Tools(repo)
    return await tools.get_stale_products(threshold_minutes=threshold_minutes)
