import contextvars
import logging

_owner_id_ctx = contextvars.ContextVar("owner_id", default=None)
logger = logging.getLogger(__name__)


def set_owner_id(owner_id: str):
    _owner_id_ctx.set(owner_id)


def get_owner_id():
    val = _owner_id_ctx.get()
    try:
        logger.info(f"[DEBUG] get_owner_id() called. Returning owner_id: {val}")
    except Exception:
        pass
    return val
