# core/agents/alert_service/repo.py
import aiosqlite, json
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from .schemas import RuleSpec, RuleRecord, Alert, Incident

class Repo:
    """
    Central persistence for the Alert Service.

    Tables:
      - rules(id, version, spec_json, enabled)
      - incidents(id, rule_id, sku, status, first_seen, last_seen, severity, title, group_key, fingerprint UNIQUE)
      - deliveries(id, incident_id, channel, ts, status, response_json)
      - settings(key PRIMARY KEY, value)
    """
    def __init__(self, path: str = "app/alert.db") -> None:
        self.path = path

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            PRAGMA busy_timeout=3000;

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
              fingerprint TEXT UNIQUE
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
            await db.commit()

    # ---------- Rules ----------
    async def list_rules(self) -> List[RuleRecord]:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT id, version, spec_json FROM rules WHERE enabled=1")
            rows = await cur.fetchall()
            return [
                RuleRecord(id=r[0], version=r[1], spec=RuleSpec(**json.loads(r[2])))
                for r in rows
            ]

    async def upsert_rule(self, spec: RuleSpec) -> None:
        async with aiosqlite.connect(self.path) as db:
            v = 1
            spec_json = json.dumps(getattr(spec, "model_dump", lambda: spec.__dict__)())
            await db.execute(
                "INSERT OR REPLACE INTO rules (id, version, spec_json, enabled) VALUES (?,?,?,?)",
                (spec.id, v, spec_json, 1 if getattr(spec, "enabled", True) else 0),
            )
            await db.commit()

    # ---------- Incidents / correlation ----------
    async def find_or_create_incident(self, alert: Alert) -> Incident:
        """Correlate by fingerprint, update last_seen or create new incident."""
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT id, status, first_seen, last_seen FROM incidents WHERE fingerprint=?",
                (alert.fingerprint,),
            )
            row = await cur.fetchone()
            ts_iso = alert.ts.isoformat()

            if row:
                await db.execute(
                    "UPDATE incidents SET last_seen=?, severity=?, title=? WHERE id=?",
                    (ts_iso, alert.severity, alert.title, row[0]),
                )
                await db.commit()
                first_seen = row[2]
                if first_seen:
                    try:
                        fs = datetime.fromisoformat(first_seen)
                        if fs.tzinfo is None:
                            fs = fs.replace(tzinfo=timezone.utc)
                    except Exception:
                        fs = alert.ts
                else:
                    fs = alert.ts
                return Incident(
                    id=row[0],
                    rule_id=alert.rule_id,
                    sku=alert.sku,
                    status="OPEN",
                    first_seen=fs,
                    last_seen=alert.ts,
                    severity=alert.severity,
                    title=alert.title,
                    group_key=alert.sku,
                )

            inc_id = f"inc_{int(alert.ts.timestamp()*1000)}"
            await db.execute(
                """
                INSERT INTO incidents
                  (id, rule_id, sku, status, first_seen, last_seen, severity, title, group_key, fingerprint)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (inc_id, alert.rule_id, alert.sku, "OPEN", ts_iso, ts_iso,
                 alert.severity, alert.title, alert.sku, alert.fingerprint),
            )
            await db.commit()
            return Incident(
                id=inc_id,
                rule_id=alert.rule_id,
                sku=alert.sku,
                status="OPEN",
                first_seen=alert.ts,
                last_seen=alert.ts,
                severity=alert.severity,
                title=alert.title,
                group_key=alert.sku,
            )

    async def is_throttled(self, fingerprint: str, dur: str) -> bool:
        """Return True if this fingerprint was seen within the given duration (e.g., '5m','1h','30s')."""
        unit = dur[-1]
        n = int(dur[:-1])
        delta = {"m": timedelta(minutes=n), "h": timedelta(hours=n), "s": timedelta(seconds=n)}[unit]
        async with aiosqlite.connect(self.path) as db:
            await db.execute("PRAGMA busy_timeout=3000;")
            cur = await db.execute("SELECT last_seen FROM incidents WHERE fingerprint=?", (fingerprint,))
            row = await cur.fetchone()
            if not row:
                return False
            last = datetime.fromisoformat(row[0])
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            return (now - last) < delta

    async def touch_incident(self, fingerprint: str) -> None:
        """Update last_seen for a fingerprint (used when throttled events arrive)."""
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO incidents(fingerprint, last_seen) VALUES(?, ?) "
                "ON CONFLICT(fingerprint) DO UPDATE SET last_seen=excluded.last_seen",
                (fingerprint, now),
            )
            await db.commit()

    async def list_incidents(self, status: Optional[str]) -> List[Dict[str, Any]]:
        q = """
        SELECT id, rule_id, sku, status, first_seen, last_seen, severity, title
        FROM incidents
        """
        args: list[Any] = []
        if status:
            q += " WHERE status=?"
            args.append(status)
        q += " ORDER BY last_seen DESC"

        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(q, args)
            rows = await cur.fetchall()
            return [
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

    async def set_status(self, inc_id: str, status: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE incidents SET status=?, last_seen=? WHERE id=?",
                (status, datetime.utcnow().isoformat(), inc_id),
            )
            await db.commit()

    # ---------- Deliveries ----------
    async def record_delivery(self, delivery_id: str, incident_id: str, channel: str,
                              status: str, response_json: Dict[str, Any] | None = None) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO deliveries (id, incident_id, channel, ts, status, response_json) "
                "VALUES (?,?,?,?,?,?)",
                (
                    delivery_id,
                    incident_id,
                    channel,
                    datetime.utcnow().isoformat(),
                    status,
                    json.dumps(response_json or {}),
                ),
            )
            await db.commit()

    # ---------- Channel settings (overrides merge with env/secrets) ----------
    async def get_channel_settings(self) -> Optional[dict]:
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute("SELECT value FROM settings WHERE key='channels'")
            row = await cur.fetchone()
            return json.loads(row[0]) if row else None

    async def save_channel_settings(self, cfg: dict) -> None:
        async with aiosqlite.connect(self.path) as db:
            val = json.dumps(cfg)
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                ("channels", val),
            )
            await db.commit()
