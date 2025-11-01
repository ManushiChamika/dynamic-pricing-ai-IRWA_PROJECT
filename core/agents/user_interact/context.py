import logging

_owner_id = None
logger = logging.getLogger(__name__)


def set_owner_id(owner_id: str):
    global _owner_id
    _owner_id = owner_id
    logger.info(f"[DEBUG] set_owner_id({owner_id})")


def get_owner_id():
    val = _owner_id
    logger.info(f"[DEBUG] get_owner_id() called. Returning owner_id: {val}")
    return val
