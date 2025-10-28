from typing import Any, Dict
from fastapi import HTTPException, Query
from core.auth_service import validate_session_token
from core.agents.data_collector.repo import DataRepo


async def get_current_user(token: str = Query(...)) -> Dict[str, Any]:
    sess = validate_session_token(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return sess


async def get_repo() -> DataRepo:
    repo = DataRepo()
    await repo.init()
    return repo
