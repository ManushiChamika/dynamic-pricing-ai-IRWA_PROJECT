from datetime import datetime, timedelta
from .schemas import Alert, Incident
from .repo import Repo

class Correlator:
    def __init__(self, repo: Repo): self.repo = repo
    async def upsert_incident(self, alert: Alert, throttle: str|None):
        # throttle by fingerprint window
        if throttle and await self.repo.is_throttled(alert.fingerprint, throttle):
            await self.repo.touch_incident(alert.fingerprint)
            return None
        inc = await self.repo.find_or_create_incident(alert)
        return inc
