# core/agents/alert_service/sinks/webhook.py
import aiohttp
from ..config import load_runtime_defaults, merge_defaults_db
from ..util.retry import retry

class WebhookSink:
    def __init__(self, repo):
        self.repo = repo

    async def send(self, incident, rule):
        # Load config with DB overrides
        db_cfg = {}
        if self.repo:
            try:
                db_cfg = await self.repo.get_channel_settings()
            except Exception:
                db_cfg = {}
        cfg = merge_defaults_db(load_runtime_defaults(), db_cfg)

        # Resolve webhook URL from dataclass or dict
        webhook = (getattr(cfg, "webhook_url", None)
                   if not isinstance(cfg, dict)
                   else cfg.get("webhook_url"))
        if not webhook:
            return  # not configured

        # Normalize incident to dict
        inc = incident if isinstance(incident, dict) else getattr(incident, "__dict__", {}) or {}

        payload = {
            "id": inc.get("id"),
            "rule_id": inc.get("rule_id"),
            "sku": inc.get("sku"),
            "severity": inc.get("severity"),
            "title": inc.get("title"),
            "status": inc.get("status", "OPEN"),
        }

        async def _post():
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as sess:
                async with sess.post(webhook, json=payload) as r:
                    body = await r.text()
                    if r.status >= 300:
                        raise Exception(f"Webhook HTTP {r.status}: {body[:200]}")

        delivery_id = f"deliv_{inc.get('id','')}_webhook"
        try:
            await retry(_post, attempts=3)
            if hasattr(self.repo, "record_delivery"):
                await self.repo.record_delivery(
                    delivery_id=delivery_id,
                    incident_id=inc.get("id", ""),
                    channel="webhook",
                    status="OK",
                    response_json={"payload": payload}
                )
        except Exception as e:
            if hasattr(self.repo, "record_delivery"):
                await self.repo.record_delivery(
                    delivery_id=delivery_id,
                    incident_id=inc.get("id", ""),
                    channel="webhook",
                    status="ERR",
                    response_json={"error": str(e)}
                )
