from .repo import Repo                            # Data access layer for rules, incidents, etc.
from .schemas import RuleSpec                     # Rule schema for validation
from pydantic import ValidationError              # For structured validation errors

class Tools:
    """
    High-level async API layer for managing alert rules, incidents, and subscriptions.
    Wraps Repo operations and provides JSON-friendly responses for a UI or HTTP API.
    """
    def __init__(self, repo: Repo):
        self.repo = repo                          # Store repository instance (DB interface)

    # ------------------------
    # RULE MANAGEMENT
    # ------------------------

    async def create_rule(self, spec_json: dict):
        """
        Create or update a rule definition.
        Validates input JSON using RuleSpec (Pydantic) before storing.
        """
        try:
            spec = RuleSpec(**spec_json)          # Validate and parse rule schema
        except ValidationError as e:
            return {"ok": False, "error": e.errors()}  # Return structured validation feedback
        await self.repo.upsert_rule(spec)         # Insert or update rule in SQLite
        return {"ok": True, "id": spec.id}        # Respond with success + rule ID

    async def list_rules(self):
        """
        Retrieve all enabled rules from the database.
        Returns list of rule specs as dictionaries.
        """
        rules = await self.repo.list_rules()
        return {"ok": True, "rules": [r.spec.dict() for r in rules]}

    # ------------------------
    # INCIDENT MANAGEMENT
    # ------------------------

    async def list_incidents(self, status: str | None = None):
        """
        Fetch incidents, optionally filtered by status (OPEN, ACKED, RESOLVED).
        """
        rows = await self.repo.list_incidents(status)
        return {"ok": True, "incidents": rows}

    async def ack_incident(self, incident_id: str):
        """
        Mark an incident as ACKED (acknowledged).
        """
        await self.repo.set_status(incident_id, "ACKED")
        return {"ok": True}

    async def resolve_incident(self, incident_id: str):
        """
        Mark an incident as RESOLVED.
        """
        await self.repo.set_status(incident_id, "RESOLVED")
        return {"ok": True}

    # ------------------------
    # ALERT LISTING (DERIVED FROM INCIDENTS)
    # ------------------------

    async def list_alerts(self, status: str = None, rule_id: str = None, limit: int = 100):
        """
        List alerts (derived from incidents table).
        Supports optional filtering by status and rule_id, with pagination limit.
        """
        try:
            incidents = await self.repo.list_incidents(status)

            # Filter results by rule_id if provided
            if rule_id:
                incidents = [inc for inc in incidents if inc.get("rule_id") == rule_id]

            # Limit number of results returned
            incidents = incidents[:limit]

            return {
                "ok": True,
                "alerts": incidents,
                "count": len(incidents)
            }
        except Exception as e:
            # Catch unexpected errors and return a safe JSON response
            return {"ok": False, "error": str(e)}

    # ------------------------
    # ALERT SUBSCRIPTIONS (SIMPLIFIED)
    # ------------------------

    async def subscribe_alerts(self, rule_id: str = None, severity: str = None, callback_url: str = None):
        """
        Subscribe an external service to alert notifications.
        (Simplified mock implementation — not persisted.)
        """
        try:
            # Simulate creating a subscription record
            subscription = {
                "id": f"sub_{hash((rule_id, severity, callback_url))}",   # Deterministic hash-based ID
                "rule_id": rule_id,                                       # Rule filter (optional)
                "severity": severity,                                     # Alert severity filter
                "callback_url": callback_url,                             # Webhook callback
                "created_at": "2024-01-01T00:00:00Z",                     # Static timestamp (for demo)
                "active": True
            }

            # Normally would persist this subscription to DB or broker
            return {
                "ok": True,
                "subscription_id": subscription["id"],
                "message": "Subscription created successfully"
            }
        except Exception as e:
            # Return JSON error safely
            return {"ok": False, "error": str(e)}
