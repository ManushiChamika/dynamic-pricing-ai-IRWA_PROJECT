# This module handles alert delivery configuration, meaning:

# Where alerts go (Slack, Email, Webhook, etc.)

# How to load these settings (from environment or Streamlit secrets)

# How to safely merge and validate configuration before use

# It’s a helper layer that ensures your alert engine can send notifications securely and correctly.


# Import required libraries
from dataclasses import dataclass, field, asdict   # for defining structured data classes
from typing import Optional, List, Dict, Any       # for type hints
import os, json                                   # for environment and JSON handling
from urllib.parse import urlparse                 # for URL validation

# It tries to read secure credentials (like API keys, SMTP passwords, webhooks) from st.secrets.
# If Streamlit isn’t available, it just sets _SECRETS = {} so the rest of the code can fall back to environment variables.
# Try to import Streamlit secrets (used in Streamlit Cloud deployments)
try:
    import streamlit as st  # type: ignore  # ignore type checker for optional import
    _SECRETS = dict(st.secrets)  # copy Streamlit secrets into a plain dictionary
except Exception:
    # If Streamlit isn't available, fall back to an empty secrets dictionary
    _SECRETS = {}

# ---------------------------------------------------------------------
# Data class that holds notification channel configuration settings
# ---------------------------------------------------------------------
@dataclass
class ChannelSettings:
    # Slack configuration
    slack_webhook_url: Optional[str] = None

    # Email (SMTP) configuration
    email_from: Optional[str] = None              # sender email address
    email_to: List[str] = field(default_factory=list)  # list of recipient emails
    smtp_host: Optional[str] = None               # SMTP server hostname
    smtp_port: int = 587                          # default port (TLS)
    smtp_user: Optional[str] = None               # SMTP username
    smtp_password: Optional[str] = None           # SMTP password (sensitive)

    # Generic webhook (custom integrations)
    webhook_url: Optional[str] = None

    # Convert settings into a dictionary (with optional password redaction)
    def as_dict(self, *, redact: bool = False) -> Dict[str, Any]:
        d = asdict(self)                          # turn dataclass into a dictionary
        if redact:
            d["smtp_password"] = None             # hide password when sending to UI/log
        return d

# ---------------------------------------------------------------------
# Helper function: get config value from Streamlit secrets or environment
# ---------------------------------------------------------------------
def _get(key: str, default: Any = None) -> Any:
    # Prefer Streamlit secrets if present, otherwise use environment variable
    if key in _SECRETS:
        return _SECRETS.get(key, default)
    return os.getenv(key, default)

# ---------------------------------------------------------------------
# Helper: parse a string into a list (handles JSON or comma-separated values)
# ---------------------------------------------------------------------
def _json_list(val: Optional[str]) -> list:
    if val in (None, ""):
        return []                                 # empty input returns an empty list
    try:
        # Try to parse JSON (e.g., '["a","b","c"]')
        v = json.loads(val) if isinstance(val, str) else val
        if isinstance(v, list):
            # Clean up whitespace and ensure all items are strings
            return [str(x).strip() for x in v if str(x).strip()]
    except Exception:
        # If parsing fails, fall back to comma-splitting
        pass
    return [s.strip() for s in str(val).split(",") if s.strip()]

# ---------------------------------------------------------------------
# Load default configuration values from environment or Streamlit secrets
# ---------------------------------------------------------------------
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

# ---------------------------------------------------------------------
# Merge database config (if any) on top of environment defaults
# ---------------------------------------------------------------------
def merge_defaults_db(defaults: ChannelSettings, db_cfg: dict | None) -> ChannelSettings:
    """DB overrides > defaults (env/secrets)."""
    if not db_cfg:
        # No database config, just validate and return defaults
        _validate(defaults)
        return defaults

    # Convert defaults to dict so we can override them
    merged = asdict(defaults)

    # Replace fields with database values if provided
    for k, v in db_cfg.items():
        if v not in (None, "", [], {}):           # skip empty or invalid values
            merged[k] = v

    # Create a new ChannelSettings object with merged values
    cfg = ChannelSettings(**merged)

    # Validate merged configuration before returning
    _validate(cfg)
    return cfg

# ---------------------------------------------------------------------
# Validate that the configuration values are correct and safe
# ---------------------------------------------------------------------
def _validate(cfg: ChannelSettings) -> None:
    # Helper to check if a URL is valid (must start with http/https)
    def _ok_url(u: Optional[str]) -> bool:
        if not u:
            return True                           # empty URLs are allowed
        try:
            p = urlparse(u)
            return p.scheme in ("http", "https")  # only allow http/https schemes
        except Exception:
            return False

    # Validate Slack webhook URL format
    if not _ok_url(cfg.slack_webhook_url):
        raise ValueError("Invalid Slack webhook URL")

    # Validate generic webhook URL format
    if not _ok_url(cfg.webhook_url):
        raise ValueError("Invalid generic webhook URL")

    # Ensure SMTP port is in the valid range (1–65535)
    if cfg.smtp_port and (int(cfg.smtp_port) <= 0 or int(cfg.smtp_port) > 65535):
        raise ValueError("Invalid SMTP port")

# ---------------------------------------------------------------------
# Prepare configuration for UI (hides secrets like passwords)
# ---------------------------------------------------------------------
def for_ui(cfg: ChannelSettings) -> Dict[str, Any]:
    """Return a UI-safe dict (password redacted)."""
    return cfg.as_dict(redact=True)
