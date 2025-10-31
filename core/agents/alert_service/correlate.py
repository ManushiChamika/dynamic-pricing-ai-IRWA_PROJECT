# In an alert system, the same issue might trigger multiple alerts in a short period (for example, “High CPU usage” every minute).
# Instead of creating hundreds of separate incidents, the Correlator groups (or “correlates”) these alerts together based on their fingerprint (a unique string per issue).

from datetime import datetime, timedelta   # Import date/time utilities (not used here yet)
from .schemas import Alert, Incident        # Import data models for Alert and Incident (custom types)
from .repo import Repo                      # Import the Repo class (handles data storage/retrieval)

# ---------------------------------------------------------------------
# Correlator class: links incoming alerts to existing or new incidents
# ---------------------------------------------------------------------
class Correlator:
    # Constructor: takes a repository instance to access alert/incident data
    def __init__(self, repo: Repo):
        self.repo = repo  # store the repository for later use

    # Main method: create or update (upsert) an incident based on an alert
    async def upsert_incident(self, alert: Alert, throttle: str | None):
        # ---------------------------------------------------------------
        # If throttling is enabled, check whether this alert is "throttled"
        # (i.e., repeated within a short window and should be ignored)
        # ---------------------------------------------------------------
        if throttle and await self.repo.is_throttled(alert.fingerprint, throttle):
            # If throttled, update ("touch") the existing incident timestamp
            await self.repo.touch_incident(alert.fingerprint)
            # Return None since no new incident is created
            return None

        # ---------------------------------------------------------------
        # Otherwise, either find an existing incident matching this alert
        # or create a new one if none exists
        # ---------------------------------------------------------------
        inc = await self.repo.find_or_create_incident(alert)

        # Return the resulting Incident object
        return inc
