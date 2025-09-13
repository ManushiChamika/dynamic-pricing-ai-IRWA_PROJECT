import streamlit as st
import plotly.express as px
import pandas as pd
import random
import os
import json
from datetime import datetime
import asyncio
import uuid
import threading
from concurrent.futures import TimeoutError as FuturesTimeout
import sys
import pathlib

# =========================
# User Interaction Agent
# =========================
try:
    from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
except Exception:
    # Fallback stub agent
    class UserInteractionAgent:
        def __init__(self, user_name: str = "User"):
            self.user_name = user_name

        def get_response(self, text: str) -> str:
            return f"(Stub agent) Hi {self.user_name}, you asked: '{text}'. " \
                   f"Replace this stub by installing the core agent package."

# ---- Streamlit Page Config ----
st.set_page_config(page_title="Dynamic Pricing Dashboard", page_icon="📊", layout="wide")

# ---- Custom CSS ----
st.markdown("""
<style>
.stApp { background-color: #a6bdde; color: #000000; }
.stMetric { background-color: #7da3c3; border-radius: 10px; padding: 10px; color: #000000; }
.stSidebar { background-color: #7da3c3; color: #000000; }
.stChatMessage { background-color: #6b92b1; color: #000000; border-radius: 10px; padding: 5px; }
.stTextInput > div > div > input { background-color: #a6bdde; color: #000000; border: 1px solid #000000; }
</style>
""", unsafe_allow_html=True)

# ====================
# Simulated Data Layer
# ====================
def get_dynamic_pricing_data() -> pd.DataFrame:
    products = ["A", "B", "C", "D", "E"]
    data = []
    for p in products:
        price = random.randint(100, 200)
        demand = random.randint(150, 500)
        data.append({"Product": p, "Price": price, "Demand": demand})
    return pd.DataFrame(data)

def get_demand_trend() -> pd.DataFrame:
    return pd.DataFrame({
        "Date": pd.date_range(start="2025-01-01", periods=12, freq="M"),
        "Demand": [random.randint(200, 400) for _ in range(12)]
    })

# ==========================
# Simple User Data Persistence
# ==========================
DATA_FILE = "user_data.json"

def load_user_data(email: str):
    """Load user data. Backward compatible with older schema that only had chat_history.

    Returns a dict with keys:
    - threads: {thread_id: {"title": str, "messages": [ {role, content, time} ] }}
    - current_thread_id: str
    - metrics: any
    - chat_history: maintained for backward compatibility (current thread messages)
    """
    empty = {"threads": {}, "current_thread_id": None, "metrics": None, "chat_history": []}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                all_data = json.load(f)
            user = all_data.get(email)
            if not user:
                return empty
            # New schema present
            if "threads" in user:
                threads = user.get("threads", {}) or {}
                current = user.get("current_thread_id")
                if not threads:
                    # Create an empty default thread
                    tid = str(uuid.uuid4())
                    threads = {tid: {"title": "New chat", "messages": []}}
                    current = tid
                if not current or current not in threads:
                    current = next(iter(threads.keys()))
                # Back-compat mirror
                ch = threads[current]["messages"]
                return {
                    "threads": threads,
                    "current_thread_id": current,
                    "metrics": user.get("metrics"),
                    "chat_history": ch,
                }
            # Old schema: migrate one linear chat_history into a default thread
            old_ch = user.get("chat_history", []) or []
            tid = str(uuid.uuid4())
            threads = {tid: {"title": "Chat 1", "messages": old_ch}}
            return {
                "threads": threads,
                "current_thread_id": tid,
                "metrics": user.get("metrics"),
                "chat_history": old_ch,
            }
        except json.JSONDecodeError:
            return empty
    return empty

def save_user_data(email: str, data: dict):
    """Save user data with backward compatibility.

    Expects keys in data: threads, current_thread_id, metrics.
    Also stores chat_history mirror of the current thread for older readers.
    """
    all_data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                all_data = json.load(f)
        except json.JSONDecodeError:
            all_data = {}

    threads = data.get("threads") or {}
    current = data.get("current_thread_id")
    if not threads:
        tid = str(uuid.uuid4())
        threads = {tid: {"title": "New chat", "messages": []}}
        current = tid
    if not current or current not in threads:
        current = next(iter(threads.keys()))

    current_messages = threads[current]["messages"]
    payload = {
        "threads": threads,
        "current_thread_id": current,
        "metrics": data.get("metrics"),
        # Back-compat mirror
        "chat_history": current_messages,
    }

    all_data[email] = payload
    with open(DATA_FILE, "w") as f:
        json.dump(all_data, f, indent=4)

# =================
# Session Gate/Init
# =================
if "session" not in st.session_state or st.session_state["session"] is None:
    st.warning("⚠ You must log in first!")
    st.stop()

user_session = st.session_state["session"]
# Get user-friendly name
user_email = user_session.get("email") or "anonymous@example.com"
full_name = user_session.get("full_name", "").strip()

if full_name:
    user_name = full_name
else:
    # Extract part before @ from email
    user_name = user_email.split("@")[0]


# Load persisted user data into session_state once (threads-aware)
if any(k not in st.session_state for k in ("threads", "current_thread_id", "metrics")):
    _loaded = load_user_data(user_email)
    st.session_state.setdefault("threads", _loaded.get("threads", {}))
    st.session_state.setdefault("current_thread_id", _loaded.get("current_thread_id"))
    st.session_state.setdefault("metrics", _loaded.get("metrics", None))
    # Backward-compat mirror of current thread
    cur = st.session_state.get("current_thread_id")
    cur_msgs = []
    if cur and cur in st.session_state["threads"]:
        cur_msgs = st.session_state["threads"][cur]["messages"]
    st.session_state.setdefault("chat_history", cur_msgs)

# Initialize agent once per user session and seed with prior chat history
AGENT_KEY = "agent"
AGENT_USER_KEY = "agent_user_email"
if (
    AGENT_KEY not in st.session_state
    or st.session_state.get(AGENT_USER_KEY) != user_email
):
    agent = UserInteractionAgent(user_name=user_name)
    # Seed agent memory from persisted chat history so LLM sees full context
    for msg in st.session_state.get("chat_history", []):
        role = msg.get("role")
        content = msg.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            try:
                agent.add_to_memory(role, content)
            except Exception:
                pass
    st.session_state[AGENT_KEY] = agent
    st.session_state[AGENT_USER_KEY] = user_email
else:
    agent = st.session_state[AGENT_KEY]

# ===================
# Dashboard Header/UI
# ===================
st.markdown(f"<h2 style='color:#000000;'>👋 Welcome back, <b>{user_name}</b></h2>", unsafe_allow_html=True)

# ---- Metrics ----
st.subheader("📈 Key Business Metrics")
df = get_dynamic_pricing_data()

total_sales = int((df["Price"] * df["Demand"]).sum())
avg_price = float(df["Price"].mean())
units_sold = int(df["Demand"].sum())

if st.session_state["metrics"] is None:
    st.session_state["metrics"] = {
        "total_sales": total_sales,
        "avg_price": avg_price,
        "units_sold": units_sold
    }

col1, col2, col3 = st.columns(3)
col1.metric(label="💰 Total Sales", value=f"${st.session_state['metrics']['total_sales']:,}", delta="+5%")
col2.metric(label="💵 Avg. Price", value=f"${st.session_state['metrics']['avg_price']:.2f}", delta="-2%")
col3.metric(label="📦 Units Sold", value=f"{st.session_state['metrics']['units_sold']:,}", delta="+8%")

st.markdown("---")

# Persist metrics
save_user_data(user_email, {
    "threads": st.session_state.get("threads", {}),
    "current_thread_id": st.session_state.get("current_thread_id"),
    "metrics": st.session_state["metrics"],
})

# ---- Charts ----
st.subheader("📊 AI Prediction: Price vs Demand")
fig = px.scatter(
    df, x="Price", y="Demand", size="Demand", color="Product",
    hover_name="Product", template="plotly_white", width=900, height=500
)
fig.update_layout(plot_bgcolor="#5896ed", paper_bgcolor="#5896ed", font_color="#000000")
st.plotly_chart(fig, use_container_width=True)

st.subheader("📈 AI Forecast: Demand Over Time")
trend_df = get_demand_trend()
fig2 = px.line(trend_df, x="Date", y="Demand", markers=True, template="plotly_white", width=900, height=400)
fig2.update_traces(line=dict(color="#FFFFFF"))
fig2.update_layout(plot_bgcolor="#5896ed", paper_bgcolor="#5896ed", font_color="#000000")
st.plotly_chart(fig2, use_container_width=True)

# ===============
# Sidebar / Chat
# ===============
st.sidebar.title("⚙ Menu")
st.sidebar.subheader("👤 User Info")
st.sidebar.info(f"Name: {user_name}\n*Email:* {user_email}")

# Chat history
st.sidebar.subheader("💬 Chats")
# Thread selection and management
threads = st.session_state.get("threads", {})
current_thread_id = st.session_state.get("current_thread_id")
if not threads:
    # Ensure at least one thread exists
    tid = str(uuid.uuid4())
    threads[tid] = {"title": "New chat", "messages": []}
    st.session_state["threads"] = threads
    st.session_state["current_thread_id"] = tid
    current_thread_id = tid

# Dropdown to pick thread
options = [(tid, data.get("title") or f"Chat {i+1}") for i, (tid, data) in enumerate(threads.items())]
labels = {tid: title for tid, title in options}
tid_list = [tid for tid, _ in options]
if current_thread_id not in threads:
    current_thread_id = tid_list[0]
selected = st.sidebar.selectbox(
    "Select conversation",
    options=tid_list,
    index=tid_list.index(current_thread_id),
    format_func=lambda tid: labels.get(tid, tid),
)
if selected != current_thread_id:
    st.session_state["current_thread_id"] = selected
    # Mirror chat_history for back-compat
    st.session_state["chat_history"] = st.session_state["threads"][selected]["messages"]

with st.sidebar.expander("Manage chats", expanded=False):
    c1, c2 = st.columns([2, 1])
    with c1:
        new_title = st.text_input("Rename current", value=labels.get(selected, ""), key="rename_thread")
    with c2:
        if st.button("Save", key="rename_thread_btn"):
            st.session_state["threads"][selected]["title"] = new_title or labels.get(selected)
    if st.button("New chat", key="new_thread_btn"):
        tid = str(uuid.uuid4())
        st.session_state["threads"][tid] = {"title": f"Chat {len(threads)+1}", "messages": []}
        st.session_state["current_thread_id"] = tid
        st.session_state["chat_history"] = []

st.sidebar.markdown("---")
st.sidebar.subheader("🗨️ Messages")
chat_container = st.sidebar.container()
for chat in st.session_state.get("threads", {}).get(st.session_state.get("current_thread_id"), {}).get("messages", []):
    role = chat.get("role")
    message = chat.get("content")
    time_str = chat.get("time", datetime.now().strftime("%H:%M:%S"))
    if role == "user":
        chat_container.markdown(f"🧑 [{time_str}] User: {message}")
    else:
        chat_container.markdown(f"🤖 [{time_str}] Bot: {message}")

# Chat input + response
user_input = st.chat_input("Ask me about pricing, demand, or sales...")
if user_input:
    msg_user = {
        "role": "user",
        "content": user_input,
        "time": datetime.now().strftime("%H:%M:%S")
    }
    # Write to current thread + mirror
    cur = st.session_state.get("current_thread_id")
    if cur and cur in st.session_state["threads"]:
        st.session_state["threads"][cur]["messages"].append(msg_user)
        st.session_state["chat_history"] = st.session_state["threads"][cur]["messages"]
    else:
        st.session_state["chat_history"].append(msg_user)
    # Keep agent memory in sync for immediate context
    try:
        agent.add_to_memory("user", user_input)
    except Exception:
        pass
    with st.chat_message("user"):
        st.markdown(user_input)

    # Call OpenRouter agent
    response = agent.get_response(user_input)
    msg_bot = {
        "role": "assistant",
        "content": response,
        "time": datetime.now().strftime("%H:%M:%S")
    }
    # Write to current thread + mirror
    cur = st.session_state.get("current_thread_id")
    if cur and cur in st.session_state["threads"]:
        st.session_state["threads"][cur]["messages"].append(msg_bot)
        st.session_state["chat_history"] = st.session_state["threads"][cur]["messages"]
    else:
        st.session_state["chat_history"].append(msg_bot)
    try:
        agent.add_to_memory("assistant", response)
    except Exception:
        pass
    with st.chat_message("assistant"):
        st.markdown(response)

    save_user_data(user_email, {
        "threads": st.session_state.get("threads", {}),
        "current_thread_id": st.session_state.get("current_thread_id"),
        "metrics": st.session_state["metrics"],
    })

# Logout
if st.sidebar.button("🚪 Logout"):
    st.session_state["session"] = None
    st.success("You have been logged out. Please refresh or go back to login.")
    st.stop()


# ============================================================================ #
# ==================  🔧 EXTRAS: Alerts Engine & Incidents  ================== #
# ============================================================================ #

# Make 'core' package importable (only if it exists)
try:
    HERE = pathlib.Path(__file__).resolve()
except NameError:
    # Fallback for some environments where _file_ may not be defined
    HERE = pathlib.Path.cwd()

ROOT = next((p for p in [HERE, *HERE.parents] if (p / "core").exists()), None)
if ROOT and str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Background asyncio loop (to call alert APIs safely from Streamlit)
def _ensure_bg_loop():
    if "_bg_loop" not in st.session_state:
        loop = asyncio.new_event_loop()
        t = threading.Thread(target=loop.run_forever, daemon=True)
        t.start()
        st.session_state["_bg_loop"] = loop
    return st.session_state["_bg_loop"]

def run_async(coro, timeout: float | None = 10.0):
    loop = _ensure_bg_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, loop)
    try:
        return fut.result(timeout=timeout)
    except FuturesTimeout:
        return None
    except Exception:
        return None

# Start alerts engine once (so incidents flow even on the dashboard)
alerts = None
try:
    from core.agents.alert_service import api as _alerts
    alerts = _alerts
except Exception:
    alerts = None

if alerts:
    if "_alerts_started" not in st.session_state:
        try:
            asyncio.run_coroutine_threadsafe(alerts.start(), _ensure_bg_loop())
            st.session_state["_alerts_started"] = True
        except Exception:
            st.session_state["_alerts_started"] = False

    with st.expander("🔔 Incidents (live — extras)", expanded=False):
        try:
            rows = run_async(alerts.list_incidents(None)) or []
        except Exception:
            rows = []
        st.metric("Open incidents", sum(1 for r in rows if r.get("status") == "OPEN"))
        if rows:
            st.dataframe(pd.DataFrame(rows))
        else:
            st.info("No incidents yet — go to Alerts & Notifications and trigger a Demo scenario.")
else:
    with st.expander("🔔 Incidents (live — extras)", expanded=False):
        st.info("Alerts service not available. Ensure core/agents/alert_service exists and dependencies are installed.")

# =============================
# 🔎 Activity Feed (High-Level)
# =============================
st.markdown("---")
st.subheader("🧠 Under-the-hood Activity")
try:
    from core.agents.agent_sdk.activity_log import activity_log
    items = activity_log.recent(50)
    if not items:
        st.info("No recent activity yet. Ask a pricing question to see the steps here.")
    else:
        for ev in items:
            status = ev.get("status", "info")
            badge = "🟢" if status == "completed" else ("🟡" if status == "in_progress" else ("🔴" if status == "failed" else "🔵"))
            with st.container():
                st.markdown(f"{badge} [{ev.get('ts')}] <b>{ev.get('agent')}</b> — {ev.get('action')} ", unsafe_allow_html=True)
                msg = ev.get("message")
                if msg:
                    st.caption(msg)
                details = ev.get("details")
                if details:
                    with st.expander("Details", expanded=False):
                        st.json(details)
except Exception:
    st.info("Activity feed unavailable. It will appear once the activity logger module is loaded.")