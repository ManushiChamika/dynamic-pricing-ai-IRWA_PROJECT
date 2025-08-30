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
