# alert pipeline orchestrator for your system — the AlertEngine.
# A class that listens to events on the bus (e.g., MARKET_TICK, PRICE_PROPOSAL),
# evaluates all matching rules, turns matches into alerts, correlates them into incidents (with throttling/dedup), 
# and delivers notifications via configured sinks (Slack/email/webhook/UI).


# core/agents/alert_service/engine.py
import json
from datetime import datetime, timezone       # for timestamping alerts
from typing import Dict, Any
from types import SimpleNamespace              # for lightweight objects with attributes

# Import internal modules for repository, rules, detectors, schemas, and sinks
from .repo import Repo                         # database access layer
from .rules import RuleRuntime                 # runtime rule evaluation logic
from .detectors import DetectorRegistry        # manages signal detectors (e.g., anomaly detection)
from .schemas import Alert                     # Alert data model
from .sinks import get_sinks                   # output channels (email, slack, webhook, etc.)

# Event bus for message passing between agents
from core.agents.agent_sdk.protocol import Topic
from core.agents.agent_sdk.bus_factory import get_bus

# Initialize the shared event bus
bus = get_bus()

# ---------------------------------------------------------------------
# AlertEngine: central orchestrator that evaluates rules and generates alerts
# ---------------------------------------------------------------------
class AlertEngine:
    def __init__(self, repo: Repo):
        self.repo = repo                              # database / rule store
        self.detectors = DetectorRegistry()            # detector manager (e.g., EWMA z-score)
        self._rules: Dict[str, RuleRuntime] = {}       # holds active rules by rule ID
        self.sinks = get_sinks(repo)                   # load all notification channels once

    # -----------------------------------------------------------------
    # Start the engine: initialize repo, load rules, and subscribe to topics
    # -----------------------------------------------------------------
    async def start(self):
        await self.repo.init()                         # initialize repository (e.g., DB tables)
        await self._load_rules()                       # load rule specs from DB

        # Subscribe to system topics for incoming data streams
        bus.subscribe(Topic.MARKET_TICK.value, self.on_tick)       # real-time market data
        bus.subscribe(Topic.PRICE_PROPOSAL.value, self.on_pp)      # pricing proposal events

        # Publish a startup alert indicating readiness
        ready = SimpleNamespace(
            ts=datetime.now(timezone.utc),
            sku="SYS",                                 # system-level SKU placeholder
            severity="info",
            title=f"AlertEngine ready ({len(self._rules)} rules)",
        )
        await bus.publish(Topic.ALERT.value, ready)

    # -----------------------------------------------------------------
    # Reload rules dynamically (e.g., when admin changes them)
    # -----------------------------------------------------------------
    async def reload_rules(self):
        await self._load_rules()

    # -----------------------------------------------------------------
    # Load rules from repository and prepare runtime objects
    # -----------------------------------------------------------------
    async def _load_rules(self):
        self._rules.clear()
        for rr in await self.repo.list_rules():
            self._rules[rr.id] = RuleRuntime(rr.spec)

    # -----------------------------------------------------------------
    # Event handler: called on market tick data
    # -----------------------------------------------------------------
    async def on_tick(self, tick):
        await self._evaluate("MARKET_TICK", tick, alias="tick")

    # -----------------------------------------------------------------
    # Event handler: called on new price proposal
    # -----------------------------------------------------------------
    async def on_pp(self, pp):
        await self._evaluate("PRICE_PROPOSAL", pp, alias="pp")

    # -----------------------------------------------------------------
    # Helper to safely convert various model objects into dictionaries
    # Supports Pydantic models, dataclasses, and plain objects
    # -----------------------------------------------------------------
    @staticmethod
    def _to_dict(obj: Any) -> Dict[str, Any]:
        fn = getattr(obj, "model_dump", None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
        fn = getattr(obj, "dict", None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
        j = getattr(obj, "model_dump_json", None)
        if callable(j):
            try:
                return json.loads(j())
            except Exception:
                pass
        # Fallback: use raw __dict__ if available
        return getattr(obj, "__dict__", {}) or {}

    # -----------------------------------------------------------------
    # Evaluate incoming event against all matching rules
    # -----------------------------------------------------------------
    async def _evaluate(self, source: str, payload: Any, alias: str):
        now = datetime.now(timezone.utc)               # current timestamp (UTC)
        for rid, rule in self._rules.items():
            # Skip rules that are not tied to this event source
            if (rule.spec.source or "").strip().upper() != source.strip().upper():
                continue

            # Run the rule evaluation (checks conditions, thresholds, etc.)
            fired = await rule.evaluate(payload, now, self.detectors, alias=alias)
            if not fired:
                continue

            # Build an alert object when a rule fires
            sku = getattr(payload, "sku", "UNKNOWN")   # get SKU or fallback
            payload_dict = self._to_dict(payload)      # serialize payload

            alert = Alert(
                id=f"a_{int(now.timestamp()*1000)}",   # unique alert ID (timestamp-based)
                rule_id=rid,                           # reference to rule
                sku=sku,                               # SKU/product identifier
                title=f"{rid} on {sku}",               # human-readable alert title
                payload=payload_dict,                  # full data payload
                severity=rule.spec.severity,           # alert severity from rule
                ts=now,                                # timestamp
                fingerprint=f"{rid}:{sku}",            # unique signature for correlation
            )

            # Attempt to correlate with existing incidents (avoid duplicates)
            inc = await self._correlate(alert, rule)
            if not inc:
                continue

            # Send the correlated incident to notification sinks (Slack/email/etc.)
            await self._deliver(inc, rule)

    # -----------------------------------------------------------------
    # Correlate alert with existing incident (throttling & deduplication)
    # -----------------------------------------------------------------
    async def _correlate(self, alert, rule):
        from .correlate import Correlator
        try:
            return await Correlator(self.repo).upsert_incident(
                alert, rule.spec.notify.throttle        # throttle window (e.g., 1h)
            )
        except Exception:
            return None

    # -----------------------------------------------------------------
    # Deliver incident notifications to configured sinks
    # -----------------------------------------------------------------
    async def _deliver(self, incident, rule):
        channels = getattr(rule.spec.notify, "channels", None) or []
        for ch in channels:
            sink = self.sinks.get(ch)                   # look up sink by channel name
            if not sink:
                continue
            await sink.send(incident, rule)             # send alert (async)
