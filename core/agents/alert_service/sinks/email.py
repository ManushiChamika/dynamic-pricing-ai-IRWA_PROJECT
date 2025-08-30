# core/agents/alert_service/sinks/email.py
import os, ssl, smtplib, asyncio
from email.message import EmailMessage
from typing import Any

from ..config import load_runtime_defaults, merge_defaults_db
from ..util.retry import retry

class EmailSink:
    def __init__(self, repo):
        self.repo = repo

    async def send(self, incident: Any, rule: Any):
        # Merge env/secrets defaults with DB overrides (repo optional)
        db_cfg = {}
        if self.repo:
            try:
                db_cfg = await self.repo.get_channel_settings()
            except Exception:
                db_cfg = {}
        cfg = merge_defaults_db(load_runtime_defaults(), db_cfg)

        def _get(name: str, default=None):
            if isinstance(cfg, dict):
                return cfg.get(name, os.getenv(name.upper(), default))
            return getattr(cfg, name, os.getenv(name.upper(), default))

        EMAIL_FROM    = _get("email_from", "alerts@yourco.com")
        EMAIL_TO      = _get("email_to", [])
        if isinstance(EMAIL_TO, str):
            EMAIL_TO = [e.strip() for e in EMAIL_TO.split(",") if e.strip()]
        SMTP_HOST     = _get("smtp_host", "smtp.gmail.com")
        SMTP_PORT     = int(_get("smtp_port", 587))
        SMTP_USER     = _get("smtp_user", EMAIL_FROM)
        SMTP_PASSWORD = _get("smtp_password", "")

        if not EMAIL_TO:
            return  # nowhere to send

        # Normalize incident to dict
        inc = incident if isinstance(incident, dict) else getattr(incident, "__dict__", {}) or {}

        subj = f"[{str(inc.get('severity','INFO')).upper()}] {inc.get('title','Alert')} (rule={inc.get('rule_id')}, sku={inc.get('sku')})"

        body_lines = [
            f"Title:      {inc.get('title')}",
            f"Severity:   {inc.get('severity')}",
            f"Rule:       {inc.get('rule_id')}",
            f"SKU:        {inc.get('sku')}",
            f"Status:     {inc.get('status','OPEN')}",
            f"Timestamp:  {inc.get('last_seen') or inc.get('ts')}",
            "",
            "Payload:",
            f"{inc.get('payload')}",
        ]
        msg = EmailMessage()
        msg["From"] = EMAIL_FROM
        msg["To"] = ", ".join(EMAIL_TO)
        msg["Subject"] = subj
        msg.set_content("\n".join(body_lines))

        ctx = ssl.create_default_context()

        def _send_sync():
            # Synchronous SMTP send (called via to_thread with retry)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
                s.ehlo()
                # Try STARTTLS if supported
                try:
                    s.starttls(context=ctx)
                    s.ehlo()
                except smtplib.SMTPException:
                    # If STARTTLS not supported, proceed without it
                    pass
                if SMTP_USER and SMTP_PASSWORD:
                    s.login(SMTP_USER, SMTP_PASSWORD)
                s.send_message(msg)

        delivery_id = f"deliv_{inc.get('id','')}_email"

        async def _send_async():
            await asyncio.to_thread(_send_sync)

        try:
            # Retry transient failures
            await retry(_send_async, attempts=3)
            if hasattr(self.repo, "record_delivery"):
                await self.repo.record_delivery(
                    delivery_id=delivery_id,
                    incident_id=inc.get("id", ""),
                    channel="email",
                    status="OK",
                    response_json={"to": EMAIL_TO, "subject": subj}
                )
        except Exception as e:
            if hasattr(self.repo, "record_delivery"):
                await self.repo.record_delivery(
                    delivery_id=delivery_id,
                    incident_id=inc.get("id", ""),
                    channel="email",
                    status="ERR",
                    response_json={"error": str(e)}
                )
