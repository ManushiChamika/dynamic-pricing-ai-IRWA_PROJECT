# Full-featured MCP server for alert service with JSON schema validation
import asyncio                         # Async event loop utilities
import inspect                         # Introspection (to detect if mcp.run is coroutine)

from datetime import datetime, timezone  # Timestamps in UTC
from typing import Optional, Dict, Any   # Type hints
from pydantic import BaseModel, ValidationError, Field  # Input validation schemas
from mcp.server.fastmcp import FastMCP                 # Fast MCP server framework

from .repo import Repo                    # Persistence layer (rules/incidents/alerts)
from .engine import AlertEngine           # Core alert evaluation engine
from .tools import Tools                  # Facade for repo/engine operations

# Auth helpers (legacy wrapper name kept): capability verification & metrics
from ..agent_sdk.auth import (
    verify_capability_legacy as verify_capability,
    get_auth_metrics,
    AuthError,
)

# Health endpoints/tools shared across services
from ..agent_sdk.health_tools import ping, version, health

mcp = FastMCP("alerts-service")          # Create MCP server instance with service name

repo = Repo()                            # Instantiate repository
engine = AlertEngine(repo)               # Attach engine to repo
tools = Tools(repo)                      # Tools layer on top of repo

# ------------------------------
# Pydantic request/DTO schemas
# ------------------------------
class ListAlertsRequest(BaseModel):
    status: Optional[str] = Field(None, pattern=r"^(active|acknowledged|resolved)$")  # optional status filter
    rule_id: Optional[str] = None                                                     # optional rule filter
    limit: int = Field(100, ge=1, le=1000)                                           # pagination guardrails

class CreateAlertRequest(BaseModel):
    spec: Dict[str, Any] = Field(..., description="Alert rule specification")        # rule spec payload

class AlertActionRequest(BaseModel):
    alert_id: str = Field(..., min_length=1)                                         # target alert/incident id

class SubscribeAlertsRequest(BaseModel):
    rule_id: Optional[str] = None
    severity: Optional[str] = Field(None, pattern=r"^(low|medium|high|critical)$")   # severity filter
    callback_url: Optional[str] = None                                               # optional webhook

# ------------------------------
# MCP tools (RPC endpoints)
# ------------------------------
@mcp.tool()
async def list_alerts(status: Optional[str] = None, rule_id: Optional[str] = None, limit: int = 100, capability_token: str = ""):
    """List active alerts with optional filtering."""
    try:
        request = ListAlertsRequest(status=status, rule_id=rule_id, limit=limit)  # validate inputs
        verify_capability(capability_token, "read")                               # auth: read scope

        # Delegate to tools layer using validated values
        result = await tools.list_alerts(
            status=request.status,
            rule_id=request.rule_id,
            limit=request.limit,
        )
        return result

    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}   # standardized error
    except (AuthError, PermissionError) as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}             # auth failure
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}         # catch-all

@mcp.tool()
async def create_alert(spec: dict, capability_token: str):
    """Create new alert rule with validation."""
    try:
        request = CreateAlertRequest(spec=spec)          # schema validation for rule spec
        verify_capability(capability_token, "create_rule")  # auth: create_rule scope

        result = await tools.create_rule(request.spec)   # persist new rule
        return result

    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except (AuthError, PermissionError) as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

@mcp.tool()
async def ack_alert(alert_id: str, capability_token: str):
    """Acknowledge alert by ID."""
    try:
        request = AlertActionRequest(alert_id=alert_id)  # validate ID presence/shape
        verify_capability(capability_token, "write")     # auth: write scope

        # Alerts map to incidents operationally
        result = await tools.ack_incident(request.alert_id)
        return result

    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except (AuthError, PermissionError) as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

@mcp.tool()
async def resolve_alert(alert_id: str, capability_token: str):
    """Resolve alert by ID."""
    try:
        request = AlertActionRequest(alert_id=alert_id)  # validate ID
        verify_capability(capability_token, "write")     # auth: write scope

        result = await tools.resolve_incident(request.alert_id)  # resolve
        return result

    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except (AuthError, PermissionError) as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

@mcp.tool()
async def subscribe_alerts(rule_id: Optional[str] = None, severity: Optional[str] = None, callback_url: Optional[str] = None, capability_token: str = ""):
    """Subscribe to alert notifications."""
    try:
        request = SubscribeAlertsRequest(rule_id=rule_id, severity=severity, callback_url=callback_url)  # validate
        verify_capability(capability_token, "read")  # auth: read scope to view/subscribe

        result = await tools.subscribe_alerts(
            rule_id=request.rule_id,
            severity=request.severity,
            callback_url=request.callback_url,
        )
        return result

    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except (AuthError, PermissionError) as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

# ------------------------------
# Legacy compatibility shims
# ------------------------------
@mcp.tool()
async def create_rule(spec: dict, capability_token: str):
    """Legacy: Create rule (use create_alert instead)."""
    return await create_alert(spec, capability_token)   # delegate to new name

@mcp.tool()
async def list_rules(capability_token: str):
    """List all alert rules."""
    try:
        verify_capability(capability_token, "read")     # auth check
        result = await tools.list_rules()               # fetch rules
        return result
    except (AuthError, PermissionError) as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

@mcp.tool()
async def list_incidents(status: Optional[str] = None, capability_token: str = ""):
    """List incidents (alerts that have been triggered)."""
    try:
        verify_capability(capability_token, "read")     # auth check
        result = await tools.list_incidents(status)     # optional status filter
        return result
    except (AuthError, PermissionError) as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

@mcp.tool()
async def ack_incident(incident_id: str, capability_token: str):
    """Legacy: Acknowledge incident (use ack_alert instead)."""
    return await ack_alert(incident_id, capability_token)  # alias

@mcp.tool()
async def resolve_incident(incident_id: str, capability_token: str):
    """Legacy: Resolve incident (use resolve_alert instead)."""
    return await resolve_alert(incident_id, capability_token)  # alias

# ------------------------------
# Health & diagnostics endpoints
# ------------------------------
@mcp.tool()
async def ping_health() -> dict:
    """Basic connectivity test."""
    return await ping()                    # quick ping

@mcp.tool()
async def version_info() -> dict:
    """Server version information."""
    return await version()                 # version metadata

@mcp.tool()
async def health_check() -> dict:
    """Detailed health status."""
    return await health("alerts", check_dependencies=True)  # deep health probe

@mcp.tool()
async def auth_metrics(capability_token: str = "") -> Dict[str, Any]:
    """Get authentication metrics for this service."""
    try:
        verify_capability(capability_token, "admin")    # privileged scope
        metrics = get_auth_metrics()                    # gather counters/latency/etc.
        return {
            "ok": True,
            "result": {
                "service": "alerts",
                "metrics": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat(),  # stamp snapshot
            },
        }
    except (AuthError, PermissionError) as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

# ------------------------------
# Server bootstrap helpers
# ------------------------------
def _call_mcp_run() -> None:
    run_fn = getattr(mcp, "run", None)           # fetch run entrypoint
    if run_fn is None:
        raise RuntimeError("FastMCP.run not available")  # defensive check
    if inspect.iscoroutinefunction(run_fn):
        asyncio.run(run_fn())                    # if coroutine: run in fresh loop
    else:
        run_fn()                                 # else: call directly (sync)

def serve() -> None:
    asyncio.run(repo.init())                     # init repo in fresh loop
    asyncio.run(engine.start())                  # start engine (subscriptions, ready event)
    _call_mcp_run()                              # start MCP server (handles requests)

# Async main for importers; avoids nested event loops by pushing MCP run to executor
async def main():
    await repo.init()
    await engine.start()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _call_mcp_run)

# CLI entrypoint
if __name__ == "__main__":
    serve()
