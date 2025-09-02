import ssl, smtplib, os
from email.message import EmailMessage
from core.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERTS_SMTP_REQUIRE_TLS

REQUIRE_TLS = str(ALERTS_SMTP_REQUIRE_TLS).strip().lower() not in {"0", "false", "no"}

def send_email(to_addr: str, subject: str, body: str, from_addr: str = None):
    from_addr = from_addr or (SMTP_USER or "alerts@example.com")
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)

    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
        s.ehlo()
        try:
            s.starttls(context=ctx)
            s.ehlo()
        except smtplib.SMTPException:
            if REQUIRE_TLS:
                raise
        if SMTP_USER and SMTP_PASSWORD:
            s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)
