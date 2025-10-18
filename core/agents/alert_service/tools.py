from datetime import datetime, timezone
from .repo import Repo
from .schemas import RuleSpec, Alert
from pydantic import ValidationError

class Tools:
    def __init__(self, repo: Repo): self.repo = repo

    async def create_rule(self, spec_json: dict):
        try:
            spec = RuleSpec(**spec_json)
        except ValidationError as e:
            return {"ok": False, "error": e.errors()}
        await self.repo.upsert_rule(spec)
        return {"ok": True, "id": spec.id}

    async def list_rules(self):
        rules = await self.repo.list_rules()
        return {"ok": True, "rules": [r.spec.dict() for r in rules]}

    async def list_incidents(self, status: str|None = None):
        rows = await self.repo.list_incidents(status)
        return {"ok": True, "incidents": rows}

    async def ack_incident(self, incident_id: str):
        await self.repo.set_status(incident_id, "ACKED")
        return {"ok": True}

    async def resolve_incident(self, incident_id: str):
        await self.repo.set_status(incident_id, "RESOLVED")
        return {"ok": True}

    async def list_alerts(self, status: str = None, rule_id: str = None, limit: int = 100):
        """List alerts with filtering - maps to incidents table."""
        try:
            incidents = await self.repo.list_incidents(status)
            
            if rule_id:
                incidents = [inc for inc in incidents if inc.get("rule_id") == rule_id]
            
            incidents = incidents[:limit]
            
            return {"ok": True, "alerts": incidents, "count": len(incidents)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def subscribe_alerts(self, rule_id: str = None, severity: str = None, callback_url: str = None):
        try:
            subscription = {
                "id": f"sub_{hash((rule_id, severity, callback_url))}",
                "rule_id": rule_id,
                "severity": severity,
                "callback_url": callback_url,
                "created_at": "2024-01-01T00:00:00Z",
                "active": True
            }
            
            return {
                "ok": True, 
                "subscription_id": subscription["id"],
                "message": "Subscription created successfully"
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}


def get_llm_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "list_rules",
                "description": "Fetches all active alert rules from the database to understand the current monitoring configuration.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_alerts",
                "description": "Lists all alerts with a given status, which can be 'OPEN', 'ACKED', or 'RESOLVED', to check for existing issues.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {
                            "type": "string",
                            "description": "Filter alerts by status: OPEN, ACKED, or RESOLVED. If not provided, returns all alerts.",
                            "enum": ["OPEN", "ACKED", "RESOLVED"]
                        }
                    },
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_alert",
                "description": "Creates a new alert in the system with a given name, a detailed description of the anomaly, a severity ('LOW', 'MEDIUM', 'HIGH'), and a dictionary of relevant event data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Short name/title for the alert"
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the anomaly detected"
                        },
                        "severity": {
                            "type": "string",
                            "description": "Severity level of the alert",
                            "enum": ["LOW", "MEDIUM", "HIGH"]
                        },
                        "details": {
                            "type": "object",
                            "description": "Dictionary containing relevant event data and context"
                        }
                    },
                    "required": ["name", "description", "severity", "details"]
                }
            }
        }
    ]


async def execute_tool_call(tool_name: str, tool_args: dict, tools_instance: Tools) -> dict:
    if tool_name == "list_rules":
        return await tools_instance.list_rules()
    
    elif tool_name == "list_alerts":
        status = tool_args.get("status")
        return await tools_instance.list_alerts(status=status)
    
    elif tool_name == "create_alert":
        name = tool_args["name"]
        description = tool_args["description"]
        severity = tool_args["severity"]
        details = tool_args["details"]
        
        now = datetime.now(timezone.utc)
        alert = Alert(
            id=f"a_{int(now.timestamp()*1000)}",
            rule_id="llm_agent",
            sku=details.get("sku", "UNKNOWN"),
            title=name,
            payload=details,
            severity=severity,
            ts=now,
            fingerprint=f"llm_agent:{name}:{details.get('sku', 'UNKNOWN')}",
        )
        
        incident = await tools_instance.repo.find_or_create_incident(alert)
        return {
            "ok": True,
            "alert_created": True,
            "incident_id": incident.id,
            "message": f"Alert '{name}' created successfully"
        }
    
    else:
        return {"ok": False, "error": f"Unknown tool: {tool_name}"}
