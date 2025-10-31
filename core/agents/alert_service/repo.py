# It uses the MCP (Model Context Protocol) framework to
#  expose all alerting operations—create rules, list 
# alerts, acknowledge or resolve incidents, and subscribe to notifications—through 
# a validated, authenticated API.


# core/agents/alert_service/repo.py

import aiosqlite, json                                  # Async SQLite client and JSON utilities
from datetime import datetime, timedelta, timezone      # Time helpers (aware/naive, deltas)
from typing import List, Optional, Dict, Any            # Type hints
from .schemas import RuleSpec, RuleRecord, Alert, Incident  # App data models

class Repo:
    def __init__(self, path: str = "app/alert.db") -> None:
        self.path = path                                 # DB file path (SQLite)

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:   # Open DB connection (async)
            await db.executescript("""                    # Create tables if they don't exist
            CREATE TABLE IF NOT EXISTS rules (
              id TEXT PRIMARY KEY,
              version INTEGER,
              spec_json TEXT,
              enabled INTEGER
            );
            CREATE TABLE IF NOT EXISTS incidents (
              id TEXT PRIMARY KEY,
              rule_id TEXT,
              sku TEXT,
              status TEXT,
              first_seen TEXT,
              last_seen TEXT,
              severity TEXT,
              title TEXT,
              group_key TEXT,
              fingerprint TEXT UNIQUE,
              owner_id TEXT
            );
            CREATE TABLE IF NOT EXISTS deliveries (
              id TEXT PRIMARY KEY,
              incident_id TEXT,
              channel TEXT,
              ts TEXT,
              status TEXT,
              response_json TEXT
            );
            CREATE TABLE IF NOT EXISTS settings (
              key TEXT PRIMARY KEY,
              value TEXT
            );
            """)
            await db.commit()                             # Persist schema changes

    # ---------- Rules ----------
    async def list_rules(self) -> List[RuleRecord]:
        async with aiosqlite.connect(self.path) as db:    # Open DB
            cur = await db.execute(                       # Query enabled rules
                "SELECT id, version, spec_json FROM rules WHERE enabled=1"
            )
            rows = await cur.fetchall()                   # Fetch all rows
            return [                                      # Map rows to RuleRecord objects
                RuleRecord(id=r[0], version=r[1], spec=RuleSpec(**json.loads(r[2])))
                for r in rows
            ]

    async def upsert_rule(self, spec: RuleSpec) -> None:
        async with aiosqlite.connect(self.path) as db:    # Open DB
            v = 1                                         # Version placeholder (could bump later)
            # Serialize RuleSpec; supports pydantic/dataclass/plain objects
            spec_json = json.dumps(
                (getattr(spec, "model_dump", None) or
                 getattr(spec, "dict", None) or
                 (lambda: spec.__dict__))()
            )
            await db.execute(                             # Insert or replace rule by id
                "INSERT OR REPLACE INTO rules (id, version, spec_json, enabled) VALUES (?,?,?,?)",
                (spec.id, v, spec_json, 1 if getattr(spec, "enabled", True) else 0),
            )
            await db.commit()                             # Save change

    # ---------- Incidents ----------
    async def find_or_create_incident(self, alert: Alert) -> Incident:
        """Correlate by fingerprint, update last_seen or create new incident."""
<<<<<<< HEAD
        async with aiosqlite.connect(self.path) as db:    # Open DB
            cur = await db.execute(                       # Look up incident by fingerprint
                "SELECT id, status, first_seen, last_seen FROM incidents WHERE fingerprint=?",
=======
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT id, status, first_seen, last_seen, owner_id FROM incidents WHERE fingerprint=?",
>>>>>>> 379c70e69f421885ef6145953fb8ca8741ed7a4e
                (alert.fingerprint,),
            )
            row = await cur.fetchone()                    # One row or None
            ts_iso = alert.ts.isoformat()                 # ISO timestamp (aware)
            if row:                                       # Existing incident path
                await db.execute(                         # Update last_seen, severity, title
                    "UPDATE incidents SET last_seen=?, severity=?, title=? WHERE id=?",
                    (ts_iso, alert.severity, alert.title, row[0]),
                )
                await db.commit()
                return Incident(                          # Return updated incident model
                    id=row[0],
                    rule_id=alert.rule_id,
                    sku=alert.sku,
                    status="OPEN",
                    first_seen=datetime.fromisoformat(row[2]),
                    last_seen=alert.ts,
                    severity=alert.severity,
                    title=alert.title,
                    group_key=alert.sku,
                    owner_id=row[4],
                )

            inc_id = f"inc_{int(alert.ts.timestamp()*1000)}"  # New incident id (ms)
            await db.execute(                             # Insert new incident
                """
                INSERT INTO incidents
                  (id, rule_id, sku, status, first_seen, last_seen, severity, title, group_key, fingerprint, owner_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (inc_id, alert.rule_id, alert.sku, "OPEN", ts_iso, ts_iso,
                 alert.severity, alert.title, alert.sku, alert.fingerprint, alert.owner_id),
            )
            await db.commit()
            return Incident(                              # Return created incident model
                id=inc_id,
                rule_id=alert.rule_id,
                sku=alert.sku,
                status="OPEN",
                first_seen=alert.ts,
                last_seen=alert.ts,
                severity=alert.severity,
                title=alert.title,
                group_key=alert.sku,
                owner_id=alert.owner_id,
            )

    async def is_throttled(self, fingerprint: str, dur: str) -> bool:
        """Return True if an incident with this fingerprint was seen within duration (e.g., '5m','1h','30s')."""
        unit = dur[-1]                                    # Duration unit (s/m/h)
        n = int(dur[:-1])                                 # Duration magnitude
        delta = {"m": timedelta(minutes=n),               # Map unit → timedelta
                 "h": timedelta(hours=n),
                 "s": timedelta(seconds=n)}[unit]
        async with aiosqlite.connect(self.path) as db:    # Open DB
            cur = await db.execute(                       # Query last_seen by fingerprint
                "SELECT last_seen FROM incidents WHERE fingerprint=?", (fingerprint,)
            )
            row = await cur.fetchone()                    # One row or None
            if not row:
                return False                              # No incident → not throttled
            last = datetime.fromisoformat(row[0])         # Parse last_seen
            now = datetime.now(timezone.utc)              # Current UTC
            # Normalize naive timestamps to UTC
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            return (now - last) < delta                   # Within window → throttled

    async def list_incidents(self, status: Optional[str], owner_id: Optional[str] = None) -> List[Dict[str, Any]]:
        q = """
        SELECT id, rule_id, sku, status, first_seen, last_seen, severity, title
        FROM incidents
<<<<<<< HEAD
        """                                               # Base query
        args: list[Any] = []                              # Params for query
        if status:                                        # Optional WHERE filter
            q += " WHERE status=?"
            args.append(status)
        q += " ORDER BY last_seen DESC"                   # Most recent first
=======
        """
        args: list[Any] = []
        conditions = []
        
        if status:
            conditions.append("status=?")
            args.append(status)
        
        if owner_id:
            conditions.append("owner_id=?")
            args.append(owner_id)
        
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        
        q += " ORDER BY last_seen DESC"
>>>>>>> 379c70e69f421885ef6145953fb8ca8741ed7a4e

        async with aiosqlite.connect(self.path) as db:    # Open DB
            cur = await db.execute(q, args)               # Execute with params
            rows = await cur.fetchall()                   # Fetch all
            return [                                      # Convert rows → dicts
                dict(
                    id=r[0],
                    rule_id=r[1],
                    sku=r[2],
                    status=r[3],
                    first_seen=r[4],
                    last_seen=r[5],
                    severity=r[6],
                    title=r[7],
                )
                for r in rows
            ]

<<<<<<< HEAD
    async def set_status(self, inc_id: str, status: str) -> None:
        async with aiosqlite.connect(self.path) as db:    # Open DB
            await db.execute(                             # Update status + touch last_seen
=======
    async def set_status(self, inc_id: str, status: str, owner_id: Optional[str] = None) -> None:
        async with aiosqlite.connect(self.path) as db:
            if owner_id:
                cur = await db.execute("SELECT owner_id FROM incidents WHERE id=?", (inc_id,))
                row = await cur.fetchone()
                if not row or str(row[0]) != str(owner_id):
                    raise ValueError("Incident not found or access denied")
            
            await db.execute(
>>>>>>> 379c70e69f421885ef6145953fb8ca8741ed7a4e
                "UPDATE incidents SET status=?, last_seen=? WHERE id=?",
                (status, datetime.now(timezone.utc).isoformat(), inc_id),
            )
            await db.commit()                             # Save

    async def touch_incident(self, fingerprint: str) -> None:
        """Update last_seen for a throttled incident by fingerprint."""
        async with aiosqlite.connect(self.path) as db:    # Open DB
            await db.execute(                             # Only update last_seen
                "UPDATE incidents SET last_seen=? WHERE fingerprint=?",
                (datetime.now(timezone.utc).isoformat(), fingerprint),
            )
            await db.commit()                             # Save

    # ---------- Deliveries (optional helpers) ----------
    async def record_delivery(self, delivery_id: str, incident_id: str, channel: str,
                              status: str, response_json: Dict[str, Any] | None = None) -> None:
        async with aiosqlite.connect(self.path) as db:    # Open DB
            await db.execute(                             # Upsert delivery row
                "INSERT OR REPLACE INTO deliveries (id, incident_id, channel, ts, status, response_json) "
                "VALUES (?,?,?,?,?,?)",
                (
                    delivery_id,
                    incident_id,
                    channel,
                    datetime.utcnow().isoformat(),        # Use UTC naive for legacy; could switch to aware
                    status,
                    json.dumps(response_json or {}),      # Store downstream response payload
                ),
            )
            await db.commit()                             # Save

    # ---------- Channel settings ----------
    async def get_channel_settings(self) -> Optional[dict]:
        """
        Returns a dict of channel overrides persisted by the UI, or None if not set.
        This gets merged over secrets/env by merge_defaults_db().
        """
        async with aiosqlite.connect(self.path) as db:    # Open DB
            cur = await db.execute(                       # Fetch 'channels' settings blob
                "SELECT value FROM settings WHERE key='channels'"
            )
            row = await cur.fetchone()
            return json.loads(row[0]) if row else None    # Decode JSON if present

    async def save_channel_settings(self, cfg: dict) -> None:
        async with aiosqlite.connect(self.path) as db:    # Open DB
            val = json.dumps(cfg)                         # Serialize config
            # upsert by primary key
            await db.execute(                             # Insert or replace settings row
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("channels", val),
            )
            await db.commit()                             # Save
