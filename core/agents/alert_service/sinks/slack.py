# core/agents/alert_service/sinks/slack.py
import aiohttp
from ..config import load_runtime_defaults, merge_defaults_db
from ..util.retry import retry

class SlackSink:
    def __init__(self, repo):
        self.repo = repo

    async def send(self, incident, rule):
        # Load config (DB overrides > runtime defaults)
        db_cfg = {}
        if self.repo:
            try:
                db_cfg = await self.repo.get_channel_settings()
            except Exception:
                db_cfg = {}
        cfg = merge_defaults_db(load_runtime_defaults(), db_cfg)

        # Resolve webhook URL from dataclass or dict
        webhook = (getattr(cfg, "slack_webhook_url", None)
                   if not isinstance(cfg, dict)
                   else cfg.get("slack_webhook_url"))
        if not webhook:
            return  # No destination configured

        # Normalize incident to dict for logging/formatting
        inc = incident if isinstance(incident, dict) else getattr(incident, "__dict__", {}) or {}
        sev = str(inc.get("severity", "INFO")).upper()
        title = inc.get("title", "Alert")
        rule_id = inc.get("rule_id")
        sku = inc.get("sku")
        text = f"[{sev}] {title} (rule={rule_id}, sku={sku})"

        # POST with retries; log outcome to deliveries table if available
        async def _post():
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as sess:
                async with sess.post(webhook, json={"text": text}) as r:
                    body = await r.text()
                    # Treat 3xx/4xx/5xx as failures so retry can kick in
                    if r.status >= 300:
                        # Raise a plain Exception to keep retry util simple and broker-agnostic
                        raise Exception(f"Slack webhook HTTP {r.status}: {body[:200]}")

        delivery_id = f"deliv_{inc.get('id','')}_slack"
        try:
            await retry(_post, attempts=3)
            if hasattr(self.repo, "record_delivery"):
                await self.repo.record_delivery(
                    delivery_id=delivery_id,
                    incident_id=inc.get("id", ""),
                    channel="slack",
                    status="OK",
                    response_json={"text": text}
                )
        except Exception as e:
            if hasattr(self.repo, "record_delivery"):
                await self.repo.record_delivery(
                    delivery_id=delivery_id,
                    incident_id=inc.get("id", ""),
                    channel="slack",
                    status="ERR",
                    response_json={"error": str(e)}
                )
