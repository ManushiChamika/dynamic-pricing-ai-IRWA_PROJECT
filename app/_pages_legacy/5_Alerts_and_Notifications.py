# pages/5_Alerts_and_Notifications.py
import os, sys, pathlib, asyncio, threading, time
from queue import SimpleQueue
from types import SimpleNamespace
from datetime import datetime, timezone

import streamlit as st

# Ensure repo root on path
HERE = pathlib.Path(__file__).resolve()
ROOT = next(p for p in [HERE, *HERE.parents] if (p / "core").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Globals
ALERT_QUEUE = SimpleQueue()

# Streamlit page config
st.set_page_config(page_title="Alerts — FluxPricer AI", page_icon="🔔", layout="wide")
st.title("🔔 Alerts & Notifications")

# Sidebar badge
st.session_state.setdefault("alert_unseen", 0)
def render_sidebar_badge():
    unseen = st.session_state.get("alert_unseen", 0)
    st.sidebar.markdown(
        """
<style>
.badge { background:#e11d48; color:#fff; border-radius:999px; padding:2px 8px; font-weight:700; font-size:12px; line-height:1.2; display:inline-block; }
.sidebar-row { display:flex; align-items:center; gap:8px; }
.badge.hidden { display:none; }
</style>""",
        unsafe_allow_html=True,
    )
    cls = "badge" if unseen else "badge hidden"
    st.sidebar.markdown(f"<div class='sidebar-row'>🔔 Alerts <span class='{cls}'>{unseen}</span></div>", unsafe_allow_html=True)

render_sidebar_badge()

# Background loop helpers
def _ensure_bg_loop():
    if "_bg_loop" not in st.session_state:
        loop = asyncio.new_event_loop()
        t = threading.Thread(target=loop.run_forever, daemon=True)
        t.start()
        st.session_state["_bg_loop"] = loop
    return st.session_state["_bg_loop"]

def run_bg(coro):
    loop = _ensure_bg_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    def _done(f):
        exc = f.exception()
        if exc:
            try: st.toast(f"Task error: {exc}")
            except Exception: pass
    fut.add_done_callback(_done)
    return fut

def run_async(coro, timeout: float | None = 15.0):
    fut = asyncio.run_coroutine_threadsafe(coro, _ensure_bg_loop())
    return fut.result(timeout=timeout)

# --- Raw SMTP test helper (STRICT) -------------------------------------------
import smtplib, ssl
from email.message import EmailMessage
def _send_test_email_raw():
    EMAIL_FROM    = os.getenv("EMAIL_FROM", "alerts@yourco.com")
    EMAIL_TO      = [e.strip() for e in os.getenv("EMAIL_TO", "").split(",") if e.strip()]
    SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER     = os.getenv("SMTP_USER", EMAIL_FROM)
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

    if not EMAIL_TO:
        raise RuntimeError("EMAIL_TO is empty")
    if not SMTP_USER or not SMTP_PASSWORD:
        raise RuntimeError("SMTP_USER / SMTP_PASSWORD missing")

    msg = EmailMessage()
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)
    msg["Subject"] = "[TEST] SMTP connectivity"
    msg.set_content("If you see this, SMTP works (raw test).")

    ctx = ssl.create_default_context()
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
        code, banner = s.ehlo()
        if not s.has_extn("starttls"):
            raise RuntimeError(f"Server does not advertise STARTTLS: {banner!r}")
        code, _ = s.starttls(context=ctx)
        if code != 220:
            raise RuntimeError(f"STARTTLS failed with code {code}")
        code, _ = s.ehlo()
        if code != 250:
            raise RuntimeError(f"EHLO after STARTTLS failed with code {code}")
        code, resp = s.login(SMTP_USER, SMTP_PASSWORD)
        if code != 235:
            raise RuntimeError(f"AUTH failed: {code} {resp}")
        s.send_message(msg)

# App imports
from app.session_utils import ensure_session_from_cookie
from core.agents.alert_service import api as alerts
from core.agents.alert_service.schemas import RuleSpec
from core.agents.agent_sdk import get_bus, Topic
bus = get_bus()

from core.agents.alert_service.sinks import get_sinks

# Session/auth
ensure_session_from_cookie()
if "session" not in st.session_state or st.session_state["session"] is None:
    st.warning("⚠️ You must log in first!")
    st.stop()

# Start alert engine once
if "_alerts_started" not in st.session_state:
    run_bg(alerts.start())
    st.session_state["_alerts_started"] = True

# Demo rules (margin breach includes email)
DEMO_RULES = [
    RuleSpec(
        id="undercut_demo",
        source="MARKET_TICK",
        where="tick.competitor_price and tick.competitor_price * 1.02 < tick.our_price",
        hold_for="10s",
        severity="warn",
        notify={"channels": ["ui"], "throttle": "0s"},
        enabled=True,
    ).dict(),
    RuleSpec(
        id="margin_breach_demo",
        source="PRICE_PROPOSAL",
        where="pp.margin < 0.12",
        severity="crit",
        notify={"channels": ["ui", "email"], "throttle": "0s"},
        enabled=True,
    ).dict(),
    RuleSpec(
        id="demand_spike_demo",
        source="MARKET_TICK",
        where="tick.demand_index >= 0.95",
        severity="info",
        notify={"channels": ["ui"], "throttle": "0s"},
        enabled=True,
    ).dict(),
]

def _ensure_demo_rules():
    """Create any missing demo rules every run (idempotent)."""
    try:
        existing = run_async(alerts.list_rules()) or []
        existing_ids = {
            (r.get("id") if isinstance(r, dict) else getattr(r, "id", None))
            for r in existing
        }
        to_create = [spec for spec in DEMO_RULES if spec["id"] not in existing_ids]
        for spec in to_create:
            run_async(alerts.create_rule(spec))
        if to_create:
            try: run_async(alerts.reload_rules())
            except Exception: pass
            st.success(f"Installed {len(to_create)} demo rule(s) ✅")
    except Exception as e:
        st.warning(f"Couldn’t ensure demo rules: {e}")

# Ensure rules are present (not only when empty)
_ensure_demo_rules()

# Show rules + whether margin rule exists
_rules_now = run_async(alerts.list_rules()) or []
_has_margin = any(
    (r.get("id") if isinstance(r, dict) else getattr(r, "id", None)) == "margin_breach_demo"
    for r in _rules_now
)
st.caption(f"Rules loaded: {len(_rules_now)} • margin_breach_demo: {'✅' if _has_margin else '❌'}")

# Button to force reinstall demos
if st.sidebar.button("🧰 Reinstall demo rules"):
    try:
        # Try to create all; ignore duplicates
        for spec in DEMO_RULES:
            try: run_async(alerts.create_rule(spec))
            except Exception: pass
        try: run_async(alerts.reload_rules())
        except Exception: pass
        st.sidebar.success("Demo rules reinstalled.")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Reinstall failed: {e}")

# --- Publisher that matches margin_breach_demo -------------------------------
# Evaluator binds the PRICE_PROPOSAL payload to variable 'pp', so publish the
# PROPOSAL as the *top-level* object with 'margin' attribute.
async def _fire_margin_breach_proposal(sku: str, proposed: float, cost: float):
    margin = ((proposed - cost) / proposed) if proposed else 0.0
    await bus.publish(
        Topic.PRICE_PROPOSAL.value,
        SimpleNamespace(
            ts=datetime.now(timezone.utc),
            sku=sku,
            margin=margin,          # the rule checks this
            proposed=proposed,
            cost=cost,
            title=f"Proposed price {proposed:.2f} on cost {cost:.2f} (margin {margin:.3f})",
        ),
    )

# Live sink subscription
async def _ui_sink_consumer(obj):
    try:
        if isinstance(obj, dict):
            ts = obj.get("last_seen") or obj.get("ts") or datetime.now(timezone.utc)
            sku = obj.get("sku", "N/A")
            sev = obj.get("severity", "info")
            title = obj.get("title") or obj.get("kind", "ALERT")
        else:
            ts = getattr(obj, "last_seen", None) or getattr(obj, "ts", None) or datetime.now(timezone.utc)
            sku = getattr(obj, "sku", "N/A")
            sev = getattr(obj, "severity", "info")
            title = getattr(obj, "title", getattr(obj, "kind", "ALERT"))
        ALERT_QUEUE.put(f"[{ts:%H:%M:%S}] {sev.upper()} {sku} — {title}")
    except Exception as e:
        ALERT_QUEUE.put(f"[{datetime.now(timezone.utc):%H:%M:%S}] ERROR N/A — Live sink error: {e}")

if not st.session_state.get("_alert_ui_sink_subscribed"):
    bus.subscribe(Topic.ALERT.value, _ui_sink_consumer)
    st.session_state["_alert_ui_sink_subscribed"] = True

# Drain queue, update badge
buf = st.session_state.setdefault("alert_lines", [])
new_count = 0
while not ALERT_QUEUE.empty():
    try:
        buf.append(ALERT_QUEUE.get_nowait()); new_count += 1
    except Exception:
        break
st.session_state["alert_lines"] = buf[-300:]
if new_count:
    st.session_state["alert_unseen"] = st.session_state.get("alert_unseen", 0) + new_count
    render_sidebar_badge()

# Email debug tools
SINKS = get_sinks()  # repo optional
with st.sidebar.expander("✉️ Email debug"):
    st.write(f"Sinks loaded: `{list(SINKS.keys())}`")

    show_cfg = st.checkbox("Show SMTP config (resolved)")
    if show_cfg:
        st.caption("Raw SMTP (EMAIL_*)")
        st.write({
            "EMAIL_FROM": os.getenv("EMAIL_FROM"),
            "EMAIL_TO": os.getenv("EMAIL_TO"),
            "SMTP_HOST": os.getenv("SMTP_HOST"),
            "SMTP_PORT": os.getenv("SMTP_PORT"),
            "SMTP_USER": os.getenv("SMTP_USER"),
            "SMTP_PASSWORD_set": bool(os.getenv("SMTP_PASSWORD")),
        })
        st.caption("Sinks (ALERTS_*)")
        st.write({
            "ALERTS_EMAIL_FROM": os.getenv("ALERTS_EMAIL_FROM"),
            "ALERTS_EMAIL_TO": os.getenv("ALERTS_EMAIL_TO"),
            "ALERTS_SMTP_HOST": os.getenv("ALERTS_SMTP_HOST"),
            "ALERTS_SMTP_PORT": os.getenv("ALERTS_SMTP_PORT"),
            "ALERTS_SMTP_USER": os.getenv("ALERTS_SMTP_USER"),
            "ALERTS_SMTP_PASSWORD_set": bool(os.getenv("ALERTS_SMTP_PASSWORD")),
        })

    if st.button("Raw SMTP test"):
        try:
            _send_test_email_raw()
            st.success("Raw SMTP test sent. Check your inbox.")
        except Exception as e:
            st.error(f"SMTP failed: {e}")

    if st.button("Sink test (bypass rules)"):
        email_sink = SINKS.get("email")
        if not email_sink:
            st.error("Email sink not loaded.")
        else:
            fake_incident = {
                "id": "inc_test_email",
                "ts": datetime.now(timezone.utc),
                "last_seen": datetime.now(timezone.utc),
                "sku": "TEST-SINK",
                "severity": "warn",
                "rule_id": "email_sink_test",
                "title": "Sink test alert",
                "status": "OPEN",
                "payload": {"description": "This is a sink-only test."},
            }
            class _RuleSpecLike:
                def __init__(self):
                    self.notify = SimpleNamespace(channels=["email"])
                    self.severity = "warn"
            fake_rule = SimpleNamespace(spec=_RuleSpecLike())

            fut = asyncio.run_coroutine_threadsafe(email_sink.send(fake_incident, fake_rule), _ensure_bg_loop())
            try:
                fut.result(10)
                st.success("Sink sent. Check inbox.")
            except Exception as e:
                st.error(f"Sink failed: {e}")

    if st.button("Pipeline test (bus → sinks)"):
        test_alert = SimpleNamespace(
            ts=datetime.now(timezone.utc),
            sku="TEST-PIPE",
            severity="warn",
            rule_id="pipeline_test",
            title="Pipeline test alert",
            description="End-to-end bus → sinks.",
            channels=["email", "ui"],
        )
        asyncio.run_coroutine_threadsafe(bus.publish(Topic.ALERT.value, test_alert), _ensure_bg_loop())
        st.success("Published test alert to bus. If sinks are wired, email should arrive.")

# Live / Incidents UI
tab_live, tab_inc = st.tabs(["📡 Live stream", "🗂️ Incidents"])

with tab_live:
    st.caption("Real-time messages from the alert UI sink (plus Slack/Email/Webhook if configured).")
    log = st.empty()
    st.toggle("Auto-refresh live log", value=True, key="auto_live")

    if st.button("Mark all as read"):
        st.session_state["alert_unseen"] = 0
        render_sidebar_badge()
        st.toast("Alerts marked as read")

    c1, c2 = st.columns(2)

    if c1.button("🔔 Ping UI stream"):
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        buf = st.session_state.setdefault("alert_lines", [])
        buf.append(f"[{ts}] INFO TEST — Ping from UI (local)")
        st.session_state["alert_lines"] = buf[-300:]
        obj = SimpleNamespace(ts=datetime.now(timezone.utc), sku="TEST", severity="info", title="Ping from UI (bus)")
        asyncio.run_coroutine_threadsafe(bus.publish(Topic.ALERT.value, obj), _ensure_bg_loop())
        st.toast("Ping sent")

    if c2.button("🧪 Force test proposal"):
        dyn_sku = f"SKU-{int(time.time())}"
        run_bg(_fire_margin_breach_proposal(dyn_sku, proposed=100.0, cost=95.0))  # ~0.05 margin => guaranteed breach
        st.toast(f"Published a margin-breach proposal for {dyn_sku}")

    log.code("\n".join(st.session_state.get("alert_lines", [])) or "# Alerts will appear here…")

    if st.session_state.get("auto_live", True):
        time.sleep(1)
        st.rerun()

with tab_inc:
    st.caption("Search, filter, and manage alert incidents (OPEN / ACKED / RESOLVED).")
    cols = st.columns([1.2, 1, 1, 2])
    with cols[0]:
        status = st.selectbox("Status", ["All", "OPEN", "ACKED", "RESOLVED"], index=1)

    # CHANGED: don't use on_click; call st.rerun() directly when button returns True
    with cols[1]:
        if st.button("🔄 Refresh"):
            st.rerun()

    with cols[2]:
        do_ack = st.checkbox("Instant-ack buttons", value=True)

    # Query incidents based on current filter
    rows = run_async(alerts.list_incidents(None if status == "All" else status)) or []

    # CHANGED: compute open count reliably
    open_count = len(rows) if status == "OPEN" else sum(1 for r in rows if r.get("status") == "OPEN")
    st.metric("Open incidents", open_count)

    # OPTIONAL (NEW): auto-refresh the Incidents tab itself
    auto_inc = st.toggle("Auto-refresh incidents", value=False, key="auto_inc")
    if auto_inc:
        time.sleep(1.5)
        st.rerun()

    if rows:
        for r in rows:
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([4, 1.2, 1.2, 1.6, 1.6])
                c1.markdown(f"**{r['title']}**  \n`{r['sku']}` • **{r['severity'].upper()}** • rule=`{r['rule_id']}`")
                c2.markdown(f"Status: **{r['status']}**")
                c3.markdown(f"Last: `{r['last_seen']}`")
                if do_ack and r["status"] == "OPEN":
                    if c4.button("✅ Ack", key=f"ack_{r['id']}"):
                        run_async(alerts.ack_incident(r["id"]))
                        st.toast(f"Acked {r['id']}")
                        st.rerun()  # OK here (not a callback)

                if r["status"] in ("OPEN", "ACKED"):
                    if c5.button("🟢 Resolve", key=f"res_{r['id']}"):
                        run_async(alerts.resolve_incident(r["id"]))
                        st.toast(f"Resolved {r['id']}")
                        st.rerun()  # OK here (not a callback)
    else:
        st.info("No incidents for this filter.")


with st.expander("Debug: active rules"):
    st.json(run_async(alerts.list_rules()) or [])
