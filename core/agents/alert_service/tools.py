<<<<<<< HEAD
from .repo import Repo                            # Data access layer for rules, incidents, etc.
from .schemas import RuleSpec                     # Rule schema for validation
from pydantic import ValidationError              # For structured validation errors
=======
from datetime import datetime, timezone
from typing import Optional
from .repo import Repo
from .schemas import RuleSpec, Alert
from pydantic import ValidationError
import logging
import aiosqlite

logger = logging.getLogger("alert_tools")

async def _get_owner_id_for_sku(sku: str) -> Optional[str]:
    try:
        async with aiosqlite.connect("app/data.db") as db:
            cur = await db.execute(
                "SELECT owner_id FROM product_catalog WHERE sku=? LIMIT 1",
                (sku,),
            )
            row = await cur.fetchone()
            return str(row[0]) if row else None
    except Exception as e:
        logger.warning(f"Failed to fetch owner_id for SKU {sku}: {e}")
        return None
>>>>>>> 379c70e69f421885ef6145953fb8ca8741ed7a4e

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
<<<<<<< HEAD

            # Filter results by rule_id if provided
            if rule_id:
                incidents = [inc for inc in incidents if inc.get("rule_id") == rule_id]

            # Limit number of results returned
=======
            
            if rule_id:
                incidents = [inc for inc in incidents if inc.get("rule_id") == rule_id]
            
>>>>>>> 379c70e69f421885ef6145953fb8ca8741ed7a4e
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
<<<<<<< HEAD
        """
        Subscribe an external service to alert notifications.
        (Simplified mock implementation — not persisted.)
        """
        try:
            # Simulate creating a subscription record
=======
        try:
>>>>>>> 379c70e69f421885ef6145953fb8ca8741ed7a4e
            subscription = {
                "id": f"sub_{hash((rule_id, severity, callback_url))}",   # Deterministic hash-based ID
                "rule_id": rule_id,                                       # Rule filter (optional)
                "severity": severity,                                     # Alert severity filter
                "callback_url": callback_url,                             # Webhook callback
                "created_at": "2024-01-01T00:00:00Z",                     # Static timestamp (for demo)
                "active": True
            }
<<<<<<< HEAD

            # Normally would persist this subscription to DB or broker
=======
            
>>>>>>> 379c70e69f421885ef6145953fb8ca8741ed7a4e
            return {
                "ok": True,
                "subscription_id": subscription["id"],
                "message": "Subscription created successfully"
            }
        except Exception as e:
            # Return JSON error safely
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
    logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
    
    if tool_name == "list_rules":
        result = await tools_instance.list_rules()
        logger.info(f"list_rules result: {result}")
        return result
    
    elif tool_name == "list_alerts":
        status = tool_args.get("status")
        result = await tools_instance.list_alerts(status=status)
        logger.info(f"list_alerts result: {result}")
        return result
    
    elif tool_name == "create_alert":
        name = tool_args["name"]
        description = tool_args["description"]
        severity_input = tool_args["severity"]
        details = tool_args["details"]
        
        severity_map = {"LOW": "info", "MEDIUM": "warn", "HIGH": "crit"}
        severity = severity_map.get(severity_input, "warn")
        
        sku = details.get("sku", "UNKNOWN")
        logger.info(f"Creating alert: name={name}, severity={severity_input}->{severity}, sku={sku}")
        
        owner_id = await _get_owner_id_for_sku(sku)
        
        now = datetime.now(timezone.utc)
        alert = Alert(
            id=f"a_{int(now.timestamp()*1000)}",
            rule_id="llm_agent",
            sku=sku,
            title=name,
            payload=details,
            severity=severity,
            ts=now,
            fingerprint=f"llm_agent:{name}:{sku}",
            owner_id=owner_id,
        )
        
        incident = await tools_instance.repo.find_or_create_incident(alert)
        logger.info(f"Alert created successfully: incident_id={incident.id}")
        return {
            "ok": True,
            "alert_created": True,
            "incident_id": incident.id,
            "message": f"Alert '{name}' created successfully"
        }
    
    else:
        logger.error(f"Unknown tool: {tool_name}")
        return {"ok": False, "error": f"Unknown tool: {tool_name}"}
