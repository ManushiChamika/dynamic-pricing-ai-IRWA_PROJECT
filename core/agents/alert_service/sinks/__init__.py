from __future__ import annotations
from typing import Dict, Any, Optional

from .ui import UiSink

def _maybe_add(sinks: Dict[str, Any], name: str, cls_name: str, repo):
    try:
        mod = __import__(f"core.agents.alert_service.sinks.{name}", fromlist=[cls_name])
        cls = getattr(mod, cls_name)
        try:
            sinks[name] = cls(repo)  # some sinks accept repo
        except TypeError:
            sinks[name] = cls()      # others don't
    except Exception:
        # Missing / optional sink; ignore.
        pass

def get_sinks(repo: Optional[Any] = None) -> Dict[str, Any]:
    """Return available sinks. `repo` is optional for callers that don't have it."""
    sinks: Dict[str, Any] = {"ui": UiSink()}
    _maybe_add(sinks, "email", "EmailSink", repo)
    _maybe_add(sinks, "slack", "SlackSink", repo)
    _maybe_add(sinks, "webhook", "WebhookSink", repo)
    return sinks
