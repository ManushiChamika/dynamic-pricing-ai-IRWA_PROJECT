from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
import os, json
from urllib.parse import urlparse

# If running on Streamlit Cloud, we can read st.secrets
try:
    import streamlit as st  # type: ignore
    _SECRETS = dict(st.secrets)  # copy to plain dict
except Exception:
    _SECRETS = {}

@dataclass
class ChannelSettings:
    # Slack
    slack_webhook_url: Optional[str] = None
    # Email (SMTP)
    email_from: Optional[str] = None
    email_to: List[str] = field(default_factory=list)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    # Generic webhook
    webhook_url: Optional[str] = None

    def as_dict(self, *, redact: bool = False) -> Dict[str, Any]:
        d = asdict(self)
        if redact:
            d["smtp_password"] = None  # never echo secret back to UI
        return d

def _get(key: str, default: Any = None) -> Any:
    # Prefer Streamlit Secrets if present; fallback to env
    if key in _SECRETS:
        return _SECRETS.get(key, default)
    return os.getenv(key, default)

def _json_list(val: Optional[str]) -> list:
    if val in (None, ""):
        return []
    # Accept JSON array or comma-separated string
    try:
        v = json.loads(val) if isinstance(val, str) else val
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
    except Exception:
        pass
    return [s.strip() for s in str(val).split(",") if s.strip()]

def load_runtime_defaults() -> ChannelSettings:
    """Read defaults from st.secrets or env (loaded via .env)."""
    return ChannelSettings(
        slack_webhook_url=_get("ALERTS_SLACK_WEBHOOK"),
        email_from=_get("ALERTS_EMAIL_FROM"),
        email_to=_json_list(_get("ALERTS_EMAIL_TO")),
        smtp_host=_get("ALERTS_SMTP_HOST"),
        smtp_port=int(_get("ALERTS_SMTP_PORT", 587)),
        smtp_user=_get("ALERTS_SMTP_USER"),
        smtp_password=_get("ALERTS_SMTP_PASSWORD"),
        webhook_url=_get("ALERTS_GENERIC_WEBHOOK"),
    )

def merge_defaults_db(defaults: ChannelSettings, db_cfg: dict | None) -> ChannelSettings:
    """DB overrides > defaults (env/secrets)."""
    if not db_cfg:
        _validate(defaults)
        return defaults
    merged = asdict(defaults)
    for k, v in db_cfg.items():
        if v not in (None, "", [], {}):
            merged[k] = v
    cfg = ChannelSettings(**merged)
    _validate(cfg)
    return cfg

def _validate(cfg: ChannelSettings) -> None:
    def _ok_url(u: Optional[str]) -> bool:
        if not u:
            return True
        try:
            p = urlparse(u)
            return p.scheme in ("http", "https")
        except Exception:
            return False

    if not _ok_url(cfg.slack_webhook_url):
        raise ValueError("Invalid Slack webhook URL")
    if not _ok_url(cfg.webhook_url):
        raise ValueError("Invalid generic webhook URL")
    if cfg.smtp_port and (int(cfg.smtp_port) <= 0 or int(cfg.smtp_port) > 65535):
        raise ValueError("Invalid SMTP port")

def for_ui(cfg: ChannelSettings) -> Dict[str, Any]:
    """Return a UI-safe dict (password redacted)."""
    return cfg.as_dict(redact=True)
