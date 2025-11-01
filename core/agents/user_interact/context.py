import contextvars
from typing import Optional

_owner_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("owner_id", default=None)


def set_owner_id(owner_id: str) -> None:
    _owner_id_ctx.set(owner_id)


def get_owner_id() -> Optional[str]:
    return _owner_id_ctx.get()
