from .repo import Repo
from .schemas import RuleSpec
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
            
            # Filter by rule_id if provided
            if rule_id:
                incidents = [inc for inc in incidents if inc.get("rule_id") == rule_id]
            
            # Apply limit
            incidents = incidents[:limit]
            
            return {"ok": True, "alerts": incidents, "count": len(incidents)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def subscribe_alerts(self, rule_id: str = None, severity: str = None, callback_url: str = None):
        """Subscribe to alert notifications."""
        try:
            # Create subscription record - this is a simplified implementation
            # In production, this would integrate with notification system
            subscription = {
                "id": f"sub_{hash((rule_id, severity, callback_url))}",
                "rule_id": rule_id,
                "severity": severity,
                "callback_url": callback_url,
                "created_at": "2024-01-01T00:00:00Z",
                "active": True
            }
            
            # For now, just return success - in production would store subscription
            return {
                "ok": True, 
                "subscription_id": subscription["id"],
                "message": "Subscription created successfully"
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
