# Full-featured MCP server for alert service with JSON schema validation
import asyncio, os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, ValidationError, Field
from mcp.server.fastmcp import FastMCP
from .repo import Repo
from .engine import AlertEngine
from .tools import Tools
from ..agent_sdk.auth import verify_capability_legacy as verify_capability, get_auth_metrics, AuthError
from ..agent_sdk.health_tools import ping, version, health

mcp = FastMCP("alerts-service")

repo = Repo()
engine = AlertEngine(repo)
tools = Tools(repo)

# Input validation schemas using Pydantic
class ListAlertsRequest(BaseModel):
    status: Optional[str] = Field(None, pattern=r"^(active|acknowledged|resolved)$")
    rule_id: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)

class CreateAlertRequest(BaseModel):
    spec: Dict[str, Any] = Field(..., description="Alert rule specification")

class AlertActionRequest(BaseModel):
    alert_id: str = Field(..., min_length=1)

class SubscribeAlertsRequest(BaseModel):
    rule_id: Optional[str] = None
    severity: Optional[str] = Field(None, pattern=r"^(low|medium|high|critical)$")
    callback_url: Optional[str] = None

@mcp.tool()
async def list_alerts(status: str = None, rule_id: str = None, limit: int = 100, capability_token: str = ""):
    """List active alerts with optional filtering."""
    try:
        # Validate input
        request = ListAlertsRequest(status=status, rule_id=rule_id, limit=limit)
        verify_capability(capability_token, "read")
        
        # Call tools with validated parameters
        result = await tools.list_alerts(
            status=request.status,
            rule_id=request.rule_id, 
            limit=request.limit
        )
        return result
        
    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

@mcp.tool()
async def create_alert(spec: dict, capability_token: str):
    """Create new alert rule with validation."""
    try:
        # Validate input
        request = CreateAlertRequest(spec=spec)
        verify_capability(capability_token, "create_rule")
        
        # Call existing create_rule method
        result = await tools.create_rule(request.spec)
        return result
        
    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

@mcp.tool()
async def ack_alert(alert_id: str, capability_token: str):
    """Acknowledge alert by ID."""
    try:
        # Validate input
        request = AlertActionRequest(alert_id=alert_id)
        verify_capability(capability_token, "write")
        
        # Call existing ack_incident method (alerts map to incidents)
        result = await tools.ack_incident(request.alert_id)
        return result
        
    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

@mcp.tool()
async def resolve_alert(alert_id: str, capability_token: str):
    """Resolve alert by ID."""
    try:
        # Validate input
        request = AlertActionRequest(alert_id=alert_id)
        verify_capability(capability_token, "write")
        
        # Call existing resolve_incident method (alerts map to incidents)  
        result = await tools.resolve_incident(request.alert_id)
        return result
        
    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

@mcp.tool()
async def subscribe_alerts(rule_id: str = None, severity: str = None, callback_url: str = None, capability_token: str = ""):
    """Subscribe to alert notifications."""
    try:
        # Validate input
        request = SubscribeAlertsRequest(rule_id=rule_id, severity=severity, callback_url=callback_url)
        verify_capability(capability_token, "read")
        
        # Call tools with validated parameters
        result = await tools.subscribe_alerts(
            rule_id=request.rule_id,
            severity=request.severity,
            callback_url=request.callback_url
        )
        return result
        
    except ValidationError as e:
        return {"ok": False, "error": "validation_error", "details": e.errors()}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

# Legacy compatibility methods
@mcp.tool()
async def create_rule(spec: dict, capability_token: str):
    """Legacy: Create rule (use create_alert instead)."""
    return await create_alert(spec, capability_token)

@mcp.tool()
async def list_rules(capability_token: str):
    """List all alert rules."""
    try:
        verify_capability(capability_token, "read")
        result = await tools.list_rules()
        return result
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

@mcp.tool()
async def list_incidents(status: str = None, capability_token: str = ""):
    """List incidents (alerts that have been triggered)."""
    try:
        verify_capability(capability_token, "read")
        result = await tools.list_incidents(status)
        return result
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

@mcp.tool()
async def ack_incident(incident_id: str, capability_token: str):
    """Legacy: Acknowledge incident (use ack_alert instead)."""
    return await ack_alert(incident_id, capability_token)

@mcp.tool()
async def resolve_incident(incident_id: str, capability_token: str):
    """Legacy: Resolve incident (use resolve_alert instead)."""
    return await resolve_alert(incident_id, capability_token)

# Health tools
@mcp.tool()
async def ping_health() -> dict:
    """Basic connectivity test."""
    return await ping()

@mcp.tool() 
async def version_info() -> dict:
    """Server version information."""
    return await version()

@mcp.tool()
async def health_check() -> dict:
    """Detailed health status."""
    return await health("alerts", check_dependencies=True)

@mcp.tool()
async def auth_metrics(capability_token: str = "") -> Dict[str, Any]:
    """Get authentication metrics for this service."""
    try:
        # Validate auth - requires admin scope to view metrics
        verify_capability(capability_token, "admin")
        
        metrics = get_auth_metrics()
        return {
            "ok": True,
            "result": {
                "service": "alerts",
                "metrics": metrics,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
    except AuthError as e:
        return {"ok": False, "error": "auth_error", "message": str(e)}
    except Exception as e:
        return {"ok": False, "error": "internal_error", "message": str(e)}

async def main():
    await repo.init()
    await engine.start()
    await mcp.run()

if __name__ == "__main__":
    asyncio.run(main())
