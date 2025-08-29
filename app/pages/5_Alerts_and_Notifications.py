# app/pages/5_Alerts_and_Notifications.py
# --- path bootstrap ---
import sys, pathlib
HERE = pathlib.Path(__file__).resolve()
ROOT = next(p for p in [HERE, *HERE.parents] if (p / "core").exists())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ----------------------

import asyncio, streamlit as st
from typing import List
st.set_page_config(page_title="Alerts — FluxPricer AI", page_icon="🔔", layout="wide")

from core.bus import bus
from core.protocol import Topic
from core.models import AlertEvent
from core.agents.alert_notifier import AlertNotifier, Thresholds
from core.agents.market_collector import run_market_collector as _mc
from core.agents.pricing_optimizer import run_pricing_optimizer as _po
from app.session_utils import ensure_session_from_cookie

ensure_session_from_cookie()

if not st.session_state.get("session"):
    st.warning("Please login first."); st.stop()

st.title("🔔 Alerts & Notifications")
with st.sidebar:
    st.header("Thresholds")
    undercut = st.slider("Competitor undercut ≥", 0.0, 0.20, 0.01, 0.005)
    demand = st.slider("Demand spike ≥", 0.0, 1.0, 0.80, 0.01)
    margin = st.slider("Min margin ≥", 0.0, 0.50, 0.10, 0.01)

    st.header("Channels")
    ch_ui = st.checkbox("UI stream", True)
    ch_slack = st.checkbox("Slack stub", False)
    ch_email = st.checkbox("Email stub", False)

    start_btn = st.button("Start Agents")
    stop_btn = st.button("Stop Agents")

log = st.empty()
status = st.empty()

# sinks
async def ui_sink(a: AlertEvent):
    lines: List[str] = st.session_state.setdefault("alert_lines", [])
    lines.append(f"[{a.ts:%H:%M:%S}] {a.kind} {a.sku} — {a.message} [{a.severity}]")
    st.session_state["alert_lines"] = lines[-200:]
    log.code("\n".join(st.session_state["alert_lines"]))

async def slack_stub(a: AlertEvent):
    print(f"[SLACK] #{'pricing-alerts'}: {a.kind} {a.sku} — {a.message} [{a.severity}]")

async def email_stub(a: AlertEvent):
    print(f"[EMAIL] ops@fluxpricer.ai: {a.kind} {a.sku} — {a.message} [{a.severity}]")

# ✅ subscribe only once per session to avoid duplicate alerts on rerun
if not st.session_state.get("_alert_ui_sink_subscribed"):
    bus.subscribe(Topic.ALERT.value, ui_sink)
    st.session_state["_alert_ui_sink_subscribed"] = True

async def start_agents():
    if st.session_state.get("agents_running"):
        return
    sinks = ([ui_sink] if ch_ui else []) + ([slack_stub] if ch_slack else []) + ([email_stub] if ch_email else [])
    notifier = AlertNotifier(Thresholds(undercut, demand, margin), sinks=sinks)
    await notifier.start()
    asyncio.create_task(_po())
    asyncio.create_task(_mc("SKU-123"))
    st.session_state["agents_running"] = True
    status.success("Agents running — watch alerts below.")

async def stop_agents():
    st.session_state["agents_running"] = False
    status.info("Agents stop signal sent (demo uses simple tasks).")

if start_btn:
    asyncio.get_event_loop().create_task(start_agents())
if stop_btn:
    asyncio.get_event_loop().create_task(stop_agents())

log.code("\n".join(st.session_state.get("alert_lines", [])) or "# Alerts will appear here...")
