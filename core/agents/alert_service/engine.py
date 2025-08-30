# core/agents/alert_service/engine.py
import json
from datetime import datetime, timezone
from typing import Dict, Any
from types import SimpleNamespace

from .repo import Repo
from .rules import RuleRuntime
from .detectors import DetectorRegistry
from .schemas import Alert
from .sinks import get_sinks
from core.agents.agent_sdk.protocol import Topic
from core.agents.agent_sdk.bus_factory import get_bus

bus = get_bus()

class AlertEngine:
    def __init__(self, repo: Repo):
        self.repo = repo
        self.detectors = DetectorRegistry()
        self._rules: Dict[str, RuleRuntime] = {}
        self.sinks = get_sinks(repo)  # preload once

    async def start(self):
        await self.repo.init()
        await self._load_rules()

        bus.subscribe(Topic.MARKET_TICK.value, self.on_tick)
        bus.subscribe(Topic.PRICE_PROPOSAL.value, self.on_pp)

        ready = SimpleNamespace(
            ts=datetime.now(timezone.utc),
            sku="SYS",
            severity="info",
            title=f"AlertEngine ready ({len(self._rules)} rules)",
        )
        await bus.publish(Topic.ALERT.value, ready)

    async def reload_rules(self):
        await self._load_rules()

    async def _load_rules(self):
        self._rules.clear()
        for rr in await self.repo.list_rules():
            self._rules[rr.id] = RuleRuntime(rr.spec)

    async def on_tick(self, tick):
        await self._evaluate("MARKET_TICK", tick, alias="tick")

    async def on_pp(self, pp):
        await self._evaluate("PRICE_PROPOSAL", pp, alias="pp")

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
        return getattr(obj, "__dict__", {}) or {}

    async def _evaluate(self, source: str, payload: Any, alias: str):
        now = datetime.now(timezone.utc)  # aware
        for rid, rule in self._rules.items():
            if (rule.spec.source or "").strip().upper() != source.strip().upper():
                continue
            fired = await rule.evaluate(payload, now, self.detectors, alias=alias)
            if not fired:
                continue

            sku = getattr(payload, "sku", "UNKNOWN")
            payload_dict = self._to_dict(payload)

            alert = Alert(
                id=f"a_{int(now.timestamp()*1000)}",
                rule_id=rid,
                sku=sku,
                title=f"{rid} on {sku}",
                payload=payload_dict,
                severity=rule.spec.severity,
                ts=now,
                fingerprint=f"{rid}:{sku}",
            )

            inc = await self._correlate(alert, rule)
            if not inc:
                continue
            await self._deliver(inc, rule)

    async def _correlate(self, alert, rule):
        from .correlate import Correlator
        try:
            return await Correlator(self.repo).upsert_incident(
                alert, rule.spec.notify.throttle
            )
        except Exception:
            return None

    async def _deliver(self, incident, rule):
        channels = getattr(rule.spec.notify, "channels", None) or []
        for ch in channels:
            sink = self.sinks.get(ch)
            if not sink:
                continue
            await sink.send(incident, rule)
