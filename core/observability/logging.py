from __future__ import annotations

import logging
import sys
import uuid
from typing import Optional
import contextvars
try:
    import structlog  # type: ignore
except Exception:  # pragma: no cover
    structlog = None  # type: ignore

_correlation_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)
_agent_name: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "agent_name", default=None
)


def set_correlation_id(value: str) -> None:
    _correlation_id.set(value)


def get_correlation_id() -> Optional[str]:
    return _correlation_id.get()


def new_correlation_id() -> str:
    cid = uuid.uuid4().hex
    set_correlation_id(cid)
    return cid


def _add_correlation_id(_logger, _name, event_dict):
    cid = get_correlation_id()
    if cid:
        event_dict["correlation_id"] = cid
    agent = _agent_name.get()
    if agent:
        event_dict["agent"] = agent
    return event_dict


def init_logging(agent_name: Optional[str] = None, level: str = "INFO") -> None:
    if agent_name is not None:
        _agent_name.set(agent_name)

    level_num = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(level=level_num, stream=sys.stdout)

    if structlog is None:
        # Fallback: stdlib logging with basic format
        logging.getLogger().setLevel(level_num)
        return

    processors = [
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.add_log_level,
        _add_correlation_id,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level_num),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: Optional[str] = None):
    if structlog is None:
        return logging.getLogger(name)
    logger = structlog.get_logger(name) if name else structlog.get_logger()
    agent = _agent_name.get()
    if agent:
        return logger.bind(agent=agent)
    return logger
