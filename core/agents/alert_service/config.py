# core/agents/alert_service/config.py
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Mapping, TYPE_CHECKING

# NOTE: type-only import to avoid circular import with repo.py
if TYPE_CHECKING:
    from .repo import Repo

# Keep your existing environment/secret wiring
from core.config import ENV, ALERTS_CAP_SECRET

if not ALERTS_CAP_SECRET:
    if ENV != "dev":
        raise RuntimeError("ALERTS_CAP_SECRET must be set in non-dev environments")
    SECRET = "dev-secret"
else:
    SECRET = ALERTS_CAP_SECRET

# Optional: scopes used by your UI/API guardrails
SCOPES = {"read", "write", "create_rule"}

# --------- helpers ---------
def _mask_secret(value: Optional[str]) -> Optional[str]:
    """Return a masked value for UI (keep last 4 chars)."""
    if not value:
        return value
    tail = value[-4:]
    return f"••••••••{tail}"

def _coerce_bool(val: Optional[str], default: bool = False) -> bool:
    if val is None:
        return default
    return str(val).strip().lower() in {"1", "true", "yes", "y", "on"}

def _coerce_int(val: Optional[str], default: int) -> int:
    try:
        return int(val) if val is not None else default
    except Exception:
        return default

# --------- public API expected by api.py ---------
def load_runtime_defaults() -> Dict[str, Any]:
    """
    Read channel/runtime defaults from environment variables.
    These are used when there is nothing in the DB or as base values
    that the DB can override on a per-field basis.
    """
    return {
        "throttle": {
            # time-window to suppress duplicate alerts per fingerprint
            "window": os.getenv("ALERTS_THROTTLE_WINDOW", "5m"),
            # whether throttled hits should still update last_seen
            "touch_on_throttle": _coerce_bool(os.getenv("ALERTS_THROTTLE_TOUCH"), True),
        },
        "email": {
            "enabled": _coerce_bool(os.getenv("SMTP_ENABLED"), False),
            "host": os.getenv("SMTP_HOST"),
            "port": _coerce_int(os.getenv("SMTP_PORT"), 587),
            "user": os.getenv("SMTP_USER"),
            "password": os.getenv("SMTP_PASSWORD"),
            "from": os.getenv("SMTP_FROM", os.getenv("EMAIL_FROM")),
            "use_tls": _coerce_bool(os.getenv("SMTP_USE_TLS"), True),
            "use_ssl": _coerce_bool(os.getenv("SMTP_USE_SSL"), False),
        },
        "slack": {
            "enabled": _coerce_bool(os.getenv("SLACK_ENABLED"), False),
            "bot_token": os.getenv("SLACK_BOT_TOKEN"),
            "default_channel": os.getenv("SLACK_DEFAULT_CHANNEL", "#alerts"),
        },
        "twilio": {
            "enabled": _coerce_bool(os.getenv("TWILIO_ENABLED"), False),
            "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
            "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
            "from_number": os.getenv("TWILIO_FROM"),
        },
        "webhook": {
            "enabled": _coerce_bool(os.getenv("WEBHOOK_ENABLED"), False),
            "url": os.getenv("WEBHOOK_URL"),
            "auth_header": os.getenv("WEBHOOK_AUTH_HEADER"),
        },
    }

async def merge_defaults_db(repo: "Repo") -> Dict[str, Any]:
    """
    Merge runtime defaults with DB overrides (DB wins field-by-field).
    The repo is passed in by the caller to avoid import cycles.
    """
    base = load_runtime_defaults()
    db_cfg = await repo.get_channel_settings() or {}
    # shallow merge per channel key
    merged: Dict[str, Any] = {}
    keys = set(base.keys()) | set(db_cfg.keys())
    for k in keys:
        a = base.get(k, {})
        b = db_cfg.get(k, {})
        if isinstance(a, Mapping) and isinstance(b, Mapping):
            merged[k] = {**a, **b}
        else:
            merged[k] = b if k in db_cfg else a
    return merged

def for_ui(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a UI-safe copy of configuration with secrets masked.
    Use this to show settings in Streamlit without leaking credentials.
    """
    cfg = {**cfg}

    # email
    if "email" in cfg:
        c = dict(cfg["email"])
        c["password"] = _mask_secret(c.get("password"))
        cfg["email"] = c

    # slack
    if "slack" in cfg:
        c = dict(cfg["slack"])
        c["bot_token"] = _mask_secret(c.get("bot_token"))
        cfg["slack"] = c

    # twilio
    if "twilio" in cfg:
        c = dict(cfg["twilio"])
        c["auth_token"] = _mask_secret(c.get("auth_token"))
        cfg["twilio"] = c

    # webhook
    if "webhook" in cfg:
        c = dict(cfg["webhook"])
        c["auth_header"] = _mask_secret(c.get("auth_header"))
        cfg["webhook"] = c

    return cfg
