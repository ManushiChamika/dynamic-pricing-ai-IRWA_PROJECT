import streamlit as st
import plotly.express as px
import pandas as pd
import random
import asyncio
import threading
from concurrent.futures import TimeoutError as FuturesTimeout
import sys
import pathlib

# =========================
# 1) Page Config & Theming
# =========================
st.set_page_config(page_title="Dynamic Pricing Dashboard", page_icon="📊", layout="wide")

# Tip: Prefer Streamlit's built-in theming via .streamlit/config.toml.
# The CSS below only uses stable hooks and avoids ephemeral classnames.
st.markdown(
    """
    <style>
    :root {
        --bg: #a6bdde;
        --bg-accent: #7da3c3;
        --bg-panel: #5896ed;
        --fg: #000000;
        --border: #000000;
    }
    .stApp, .stApp header, .stApp footer { background-color: var(--bg); color: var(--fg); }
    [data-testid="stSidebar"] { background-color: var(--bg-accent); color: var(--fg); }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"], [data-testid="stMetricDelta"] { color: var(--fg); }
    [data-testid="stMetric"] { background-color: var(--bg-accent); border-radius: 12px; padding: 10px; }
    /* Inputs */
    input, textarea, select { background-color: var(--bg); color: var(--fg); border: 1px solid var(--border); }
    /* Chat messages */
    [data-testid="stChatMessage"] { background-color: #6b92b1; color: var(--fg); border-radius: 10px; padding: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================================
# 2) Data Generators (cached for reruns)
# ======================================
@st.cache_data(show_spinner=False)
def get_dynamic_pricing_data(seed: int | None = None) -> pd.DataFrame:
    if seed is not None:
        random.seed(seed)
    products = ["A", "B", "C", "D", "E"]
    data = []
    for p in products:
        price = random.randint(100, 200)
        demand = random.randint(150, 500)
        data.append({"Product": p, "Price": price, "Demand": demand})
    return pd.DataFrame(data)

@st.cache_data(show_spinner=False)
def get_demand_trend(seed: int | None = None) -> pd.DataFrame:
    if seed is not None:
        random.seed(seed + 42)
    return pd.DataFrame({
        "Date": pd.date_range(start="2025-01-01", periods=12, freq="M"),
        "Demand": [random.randint(200, 400) for _ in range(12)],
    })


# =======================
# 3) Toy AI Chat Response
# =======================
def ai_chat_response(user_input: str) -> str:
    text = user_input.lower()
    if "price" in text:
        return "💡 The AI suggests adjusting prices based on demand trends to maximize profit."
    if "demand" in text:
        return "📊 Current demand is rising. AI recommends monitoring seasonal patterns."
    if "hello" in text:
        return "👋 Hello! I’m your Dynamic Pricing Assistant. Ask me about sales, demand, or prices."
    return "🤖 Sorry, I didn’t understand. Try asking about **price**, **demand**, or **sales**."


# ==================
# 4) Session Guard
# ==================
# Expect a dict-like object in st.session_state["session"] created by the login flow.
session = st.session_state.get("session")
if not session:
    st.warning("⚠️ You must log in first!")
    st.stop()

user_name = session.get("full_name", "User")
user_email = session.get("email", "-")

# =====================
# 5) Dashboard Header
# =====================
st.markdown(f"<h2 style='color:#000000;'>👋 Welcome back, <b>{user_name}</b></h2>", unsafe_allow_html=True)

# =====================
# 6) Metrics Section
# =====================
seed = st.session_state.get("rng_seed", 1234)
df = get_dynamic_pricing_data(seed)
col1, col2, col3 = st.columns(3)
col1.metric(label="💰 Total Sales", value=f"${df['Price'].sum() * 1000:,}", delta="+5%")
col2.metric(label="💵 Avg. Price",  value=f"${df['Price'].mean():.2f}",     delta="-2%")
col3.metric(label="📦 Units Sold",  value=f"{df['Demand'].sum():,}",        delta="+8%")
st.markdown("---")


# =====================================
# 7) Tabs: Charts & AI Chat Assistant
# =====================================
tab1, tab2 = st.tabs(["📊 Charts", "💬 AI Chat Assistant"])

with tab1:
    st.subheader("💡 AI Prediction: Price vs Demand")
    fig = px.scatter(
        df, x="Price", y="Demand", size="Demand", color="Product",
        hover_name="Product",
        template="plotly_white",
        width=900, height=500,
    )
    fig.update_layout(
        plot_bgcolor="#5896ed",
        paper_bgcolor="#5896ed",
        font_color="#000000",
        xaxis=dict(gridcolor="#a6bdde", title_font_color="#000000", tickfont_color="#000000"),
        yaxis=dict(gridcolor="#a6bdde", title_font_color="#000000", tickfont_color="#000000"),
        legend=dict(font_color="#000000"),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 AI Forecast: Demand Over Time")
    trend_df = get_demand_trend(seed)
    fig2 = px.line(
        trend_df, x="Date", y="Demand", markers=True,
        template="plotly_white",
        width=900, height=400,
    )
    fig2.update_traces(line=dict(width=3))  # keep default color for contrast
    fig2.update_layout(
        plot_bgcolor="#5896ed",
        paper_bgcolor="#5896ed",
        font_color="#000000",
        xaxis=dict(gridcolor="#a6bdde", title_font_color="#000000", tickfont_color="#000000"),
        yaxis=dict(gridcolor="#a6bdde", title_font_color="#000000", tickfont_color="#000000"),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab2:
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for chat in st.session_state["chat_history"]:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    user_input = st.chat_input("Ask me about pricing, demand, or sales...")
    if user_input:
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        response = ai_chat_response(user_input)
        st.session_state["chat_history"].append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# ==============
# 8) Sidebar
# ==============
st.sidebar.title("⚙️ Menu")
st.sidebar.subheader("👤 User Info")
st.sidebar.info(f"**Name:** {user_name}\n**Email:** {user_email}")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    # Clear only auth-related keys to avoid nuking other state if you don't want to
    st.session_state.pop("session", None)
    st.success("You have been logged out.")
    st.rerun()

# ============================================================================ #
# ==================  🔧 EXTRAS: Alerts Engine & Incidents  ================== #
# ============================================================================ #

# Make 'core' package importable (only if it exists)
HERE = pathlib.Path(__file__).resolve()
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
        asyncio.run_coroutine_threadsafe(alerts.start(), _ensure_bg_loop())
        st.session_state["_alerts_started"] = True

    with st.expander("🔔 Incidents (live — extras)", expanded=False):
        rows = run_async(alerts.list_incidents(None)) or []
        st.metric("Open incidents", sum(1 for r in rows if r.get("status") == "OPEN"))
        if rows:
            st.dataframe(pd.DataFrame(rows))
        else:
            st.info("No incidents yet — go to **Alerts & Notifications** and trigger a Demo scenario.")
else:
    with st.expander("🔔 Incidents (live — extras)", expanded=False):
        st.info("Alerts service not available. Ensure `core/agents/alert_service` exists and dependencies are installed.")
