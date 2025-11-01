import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from types import SimpleNamespace
import aiosqlite

from .repo import Repo
from .rules import RuleRuntime
from .detectors import DetectorRegistry
from .schemas import Alert
from .sinks import get_sinks
from .tools import Tools, get_llm_tools, execute_tool_call
from core.agents.agent_sdk.protocol import Topic
from core.agents.agent_sdk.bus_factory import get_bus

bus = get_bus()

SYSTEM_PROMPT = """You are a vigilant Security and Anomaly Detection Agent for a dynamic pricing system. Your primary goal is to monitor system events and identify potential risks. You MUST evaluate every event against known rules and general best practices to find anomalies.

When analyzing events:
1. ALWAYS start by calling list_rules() to understand configured thresholds
2. Look for critical anomalies such as:
   - Margins below 5% (critical profit risk)
   - Negative margins (selling at a loss)
   - Any suspicious pricing patterns
3. If you detect ANY anomaly, you MUST create an alert with create_alert()
4. Be proactive - err on the side of creating alerts for potential issues

IMPORTANT: Your job is to CREATE ALERTS when you see anomalies. A margin of 2% is critically low and MUST trigger an alert."""

class AlertEngine:
    def __init__(self, repo: Repo):
        self.repo = repo
        self.detectors = DetectorRegistry()
        self._rules: Dict[str, RuleRuntime] = {}
        self.sinks = get_sinks(repo)
        self.tools = Tools(repo)
        self.llm = None
        self.logger = logging.getLogger("alert_engine")
        
        try:
            from core.agents.llm_client import get_llm_client
            self.llm = get_llm_client()
            if self.llm and self.llm.is_available():
                self.logger.info("LLM brain initialized successfully")
            else:
                self.logger.warning("LLM unavailable, AlertEngine will use rule-based mode only")
        except Exception as e:
            self.logger.warning(f"Failed to initialize LLM: {e}")

    async def start(self):
        await self.repo.init()
        await self._load_rules()

        bus.subscribe(Topic.MARKET_TICK.value, self.on_tick)
        bus.subscribe(Topic.PRICE_PROPOSAL.value, self.on_pp)

        ready = SimpleNamespace(
            ts=datetime.now(timezone.utc),
            sku="SYS",
            severity="info",
            title=f"AlertEngine ready ({len(self._rules)} rules, LLM={'enabled' if self.llm and self.llm.is_available() else 'disabled'})",
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
        await self._evaluate_with_llm("PRICE_PROPOSAL", pp)
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

    async def _evaluate_with_llm(self, source: str, payload: Any):
        if not self.llm or not self.llm.is_available():
            return

        try:
            payload_dict = self._to_dict(payload)
            
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            event_summary = json.dumps(payload_dict, indent=2, default=json_serializer)
            
            prompt = f"""A new {source} event has just been published. You need to analyze it and determine if an alert should be created.

Event Data:
```json
{event_summary}
```

Based on your analysis, determine if this event represents an anomaly that requires an alert. Remember:
- Margins below 5% are concerning
- Margins below 3% are CRITICAL
- You should err on the side of creating alerts

Use your tools to investigate and take action."""

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            tools_schema = get_llm_tools()
            
            
            async def create_alert_async(name: str, description: str, severity: str, details: dict):
                return await execute_tool_call("create_alert", {
                    "name": name, "description": description, 
                    "severity": severity, "details": details
                }, self.tools)
            
            async def list_alerts_async(status: str = None):
                return await execute_tool_call("list_alerts", {"status": status}, self.tools)
            
            async def list_rules_async():
                return await execute_tool_call("list_rules", {}, self.tools)
            
            functions_map = {
                "create_alert": create_alert_async,
                "list_alerts": list_alerts_async,
                "list_rules": list_rules_async
            }
            
            try:
                result = self.llm.chat_with_tools(
                    messages=messages, 
                    tools=tools_schema,
                    functions_map=functions_map,
                    max_rounds=3,
                    max_tokens=1000
                )
                
                self.logger.info(f"LLM response: {result}")
                    
            except Exception as e:
                self.logger.error(f"LLM tool call failed: {e}")
                
        except Exception as e:
            self.logger.error(f"LLM evaluation failed: {e}")

    async def _evaluate(self, source: str, payload: Any, alias: str):
        now = datetime.now(timezone.utc)
        for rid, rule in self._rules.items():
            if (rule.spec.source or "").strip().upper() != source.strip().upper():
                continue
            fired = await rule.evaluate(payload, now, self.detectors, alias=alias)
            if not fired:
                continue

            sku = getattr(payload, "sku", "UNKNOWN")
            payload_dict = self._to_dict(payload)
            
            owner_id = await self._get_owner_id_for_sku(sku)

            alert = Alert(
                id=f"a_{int(now.timestamp()*1000)}",
                rule_id=rid,
                sku=sku,
                title=f"{rid} on {sku}",
                payload=payload_dict,
                severity=rule.spec.severity,
                ts=now,
                fingerprint=f"{rid}:{sku}",
                owner_id=owner_id,
            )

            inc = await self._correlate(alert, rule)
            if not inc:
                continue
            await self._deliver(inc, rule)
    
    async def _get_owner_id_for_sku(self, sku: str) -> Optional[str]:
        try:
            async with aiosqlite.connect("app/data.db") as db:
                cur = await db.execute(
                    "SELECT owner_id FROM product_catalog WHERE sku=? LIMIT 1",
                    (sku,),
                )
                row = await cur.fetchone()
                return str(row[0]) if row else None
        except Exception as e:
            self.logger.warning(f"Failed to fetch owner_id for SKU {sku}: {e}")
            return None

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
