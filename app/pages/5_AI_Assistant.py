import streamlit as st
import os
import json
import uuid
from datetime import datetime

# ---- Page Config ----
st.set_page_config(page_title="AI Assistant - Dynamic Pricing", page_icon="🤖", layout="wide")

# ---- Custom CSS ----
st.markdown("""
<style>
.stApp { background-color: #a6bdde; color: #000000; }
.stMetric { background-color: #7da3c3; border-radius: 10px; padding: 10px; color: #000000; }
.stSidebar { background-color: #7da3c3; color: #000000; }
.stChatMessage { background-color: #6b92b1; color: #000000; border-radius: 10px; padding: 5px; }
.stTextInput > div > div > input { background-color: #a6bdde; color: #000000; border: 1px solid #000000; }

/* Chat bubble styles */
.user-message {
    background-color: #7da3c3;
    border-radius: 12px;
    padding: 12px 16px;
    margin: 8px 0;
    max-width: 80%;
    margin-left: auto;
    margin-right: 0;
    color: #000000;
}
.assistant-message {
    background-color: #a6bdde;
    border-radius: 12px;
    padding: 12px 16px;
    margin: 8px 0;
    max-width: 80%;
    margin-left: 0;
    margin-right: auto;
    color: #000000;
}
.message-header {
    font-weight: bold;
    margin-bottom: 4px;
    font-size: 0.9em;
}
.message-content {
    margin: 0;
}
</style>
""", unsafe_allow_html=True)

# =========================
# Optional agent dependency
# =========================
try:
    from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
except Exception:
    # Safe fallback so the app still runs if the import isn't available
    class UserInteractionAgent:
        def __init__(self, user_name: str = "User", model_name: str = "stub"):
            self.user_name = user_name
            self.model_name = model_name

        def get_response(self, text: str) -> str:
            return f"(Stub agent) Hi {self.user_name}, you asked: '{text}'. " \
                   f"Replace this stub by installing the core agent package."
        
        def add_to_memory(self, role: str, content: str):
            pass

# ==========================
# User Data Persistence
# ==========================
DATA_FILE = "user_data.json"

def load_user_data(email: str):
    """Load user data with thread support"""
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
    """Save user data with backward compatibility"""
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
user_name = user_session.get("full_name", "User")
user_email = user_session.get("email") or "anonymous@example.com"
full_name = (user_session.get("full_name") or "").strip()

if full_name:
    user_name = full_name
else:
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

# ====================
# Page Header
# ====================
st.markdown(f"<h1 style='color:#000000;'>🤖 AI Assistant</h1>", unsafe_allow_html=True)
st.markdown(f"<h3 style='color:#000000;'>Chat with FluxPricer AI, <b>{user_name}</b></h3>", unsafe_allow_html=True)

# Navigation
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/3_Dashboard.py")
with col2:
    if st.button("📊 Analytics", use_container_width=True):
        st.switch_page("pages/4_Analytics.py")
with col3:
    st.button("🤖 AI Assistant", disabled=True, use_container_width=True)
with col4:
    if st.button("📋 Activity", use_container_width=True):
        st.switch_page("pages/6_Activity.py")

st.markdown("---")

# ===============
# Sidebar / Thread Management
# ===============
st.sidebar.title("💬 FluxPricer AI")
st.sidebar.subheader("👤 User Info")
st.sidebar.info(f"Name: {user_name}\n*Email:* {user_email}")

# New conversation button prominently placed
if st.sidebar.button("➕ New Chat", key="new_thread_btn"):
    tid = str(uuid.uuid4())
    st.session_state["threads"][tid] = {"title": "New Chat", "messages": []}
    st.session_state["current_thread_id"] = tid
    st.session_state["chat_history"] = []
    st.rerun()

# Thread list with better UI
st.sidebar.subheader("Your Chats")
threads = st.session_state.get("threads", {})
current_thread_id = st.session_state.get("current_thread_id")

if not threads:
    # Ensure at least one thread exists
    tid = str(uuid.uuid4())
    threads[tid] = {"title": "New Chat", "messages": []}
    st.session_state["threads"] = threads
    st.session_state["current_thread_id"] = tid
    current_thread_id = tid

# Create a selectbox for thread selection instead of multiple buttons to avoid conflicts
thread_options = {}
for tid, data in threads.items():
    # Get preview of last message
    messages = data.get("messages", [])
    last_message = messages[-1]["content"] if messages else "No messages yet"
    last_message_preview = last_message[:30] + "..." if len(last_message) > 30 else last_message
    thread_title = data.get("title", f"Chat {list(threads.keys()).index(tid) + 1}")
    thread_options[tid] = f"{thread_title} - {last_message_preview}"

# Selectbox for thread switching
selected_thread_id = st.sidebar.selectbox(
    "Select a conversation:",
    options=list(thread_options.keys()),
    format_func=lambda x: thread_options[x],
    key="thread_selector",
    index=list(thread_options.keys()).index(current_thread_id) if current_thread_id in thread_options else 0
)

# Update current thread if selection changes
if selected_thread_id != current_thread_id:
    st.session_state["current_thread_id"] = selected_thread_id
    st.session_state["chat_history"] = st.session_state["threads"][selected_thread_id]["messages"]

# Make sure current thread exists in session state
if current_thread_id and current_thread_id not in st.session_state.get("threads", {}):
    if st.session_state.get("threads"):
        # Pick the first available thread
        first_thread_id = next(iter(st.session_state["threads"]))
        st.session_state["current_thread_id"] = first_thread_id
        st.session_state["chat_history"] = st.session_state["threads"][first_thread_id]["messages"]
    else:
        # Create a new thread if none exist
        tid = str(uuid.uuid4())
        st.session_state["threads"][tid] = {"title": "New Chat", "messages": []}
        st.session_state["current_thread_id"] = tid
        st.session_state["chat_history"] = []

# Thread management options
if current_thread_id and current_thread_id in threads:
    with st.sidebar.expander("Manage Current Chat", expanded=False):
        # Rename current thread
        current_title = threads[current_thread_id].get("title", f"Chat {len(threads)}")
        new_title = st.text_input("Rename chat", value=current_title, key="rename_thread")
        if st.button("Save Title", key="rename_thread_btn"):
            st.session_state["threads"][current_thread_id]["title"] = new_title or current_title
        
        # Delete current thread
        if st.button("🗑️ Delete Chat", key="delete_thread_btn"):
            del st.session_state["threads"][current_thread_id]
            # Switch to another thread or create a new one
            remaining_threads = list(st.session_state["threads"].keys())
            if remaining_threads:
                st.session_state["current_thread_id"] = remaining_threads[0]
                st.session_state["chat_history"] = st.session_state["threads"][remaining_threads[0]]["messages"]
            else:
                tid = str(uuid.uuid4())
                st.session_state["threads"][tid] = {"title": "New Chat", "messages": []}
                st.session_state["current_thread_id"] = tid
                st.session_state["chat_history"] = []
            st.rerun()

# AI Assistant Info
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Assistant Info")
st.sidebar.info("""
**FluxPricer AI** can help you with:
- Pricing strategies & optimization
- Market analysis & trends
- Demand forecasting
- Competitive intelligence
- Revenue optimization
- Product recommendations
""")

# ==================
# Main Chat Interface
# ==================

# Display chat messages for the current thread
current_thread_messages = st.session_state.get("threads", {}).get(st.session_state.get("current_thread_id"), {}).get("messages", [])
chat_container = st.container()

with chat_container:
    if not current_thread_messages:
        st.markdown("""
        <div style='text-align: center; padding: 40px; background-color: #7da3c3; border-radius: 15px; margin: 20px 0;'>
            <h3 style='color: #000000; margin-bottom: 15px;'>👋 Welcome to FluxPricer AI!</h3>
            <p style='color: #000000; font-size: 16px; margin-bottom: 10px;'>I'm here to help with your pricing and business questions.</p>
            <p style='color: #000000; font-size: 14px;'>Try asking me about:</p>
            <ul style='text-align: left; max-width: 400px; margin: 15px auto; color: #000000;'>
                <li>🎯 "What's the optimal price for Product A?"</li>
                <li>📈 "Analyze our current pricing strategy"</li>
                <li>🔮 "Predict demand for next quarter"</li>
                <li>🏆 "How are we competing in the market?"</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in current_thread_messages:
            role = msg.get("role")
            content = msg.get("content")
            time_str = msg.get("time", datetime.now().strftime("%H:%M:%S"))
            
            if role == "user":
                st.markdown(f"""
                <div class="user-message">
                    <div class="message-header">👤 You · {time_str}</div>
                    <div class="message-content">{content}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="assistant-message">
                    <div class="message-header">🤖 FluxPricer AI · {time_str}</div>
                    <div class="message-content">{content}</div>
                </div>
                """, unsafe_allow_html=True)

# Chat input + response
user_input = st.chat_input("Ask me about pricing, demand, sales, or market analysis...")
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
    
    # Display user message
    st.markdown(f"""
    <div class="user-message">
        <div class="message-header">👤 You · {msg_user['time']}</div>
        <div class="message-content">{msg_user['content']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Show loading indicator while processing
    with st.spinner("🤖 FluxPricer AI is thinking..."):
        try:
            response = agent.get_response(user_input)
        except Exception as e:
            response = f"I apologize, but I encountered an error processing your request: {e}"
    
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
    
    # Display assistant message
    st.markdown(f"""
    <div class="assistant-message">
        <div class="message-header">🤖 FluxPricer AI · {msg_bot['time']}</div>
        <div class="message-content">{msg_bot['content']}</div>
    </div>
    """, unsafe_allow_html=True)

    save_user_data(user_email, {
        "threads": st.session_state.get("threads", {}),
        "current_thread_id": st.session_state.get("current_thread_id"),
        "metrics": st.session_state.get("metrics"),
    })

# ==================
# Quick Actions
# ==================
st.markdown("---")
st.subheader("🚀 Quick Actions")

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("💡 Get Pricing Insights", use_container_width=True):
        insight_prompt = "Please analyze our current pricing strategy and provide actionable insights."
        st.session_state["quick_action_prompt"] = insight_prompt

with col2:
    if st.button("📊 Market Analysis", use_container_width=True):
        market_prompt = "Provide a comprehensive market analysis for our products."
        st.session_state["quick_action_prompt"] = market_prompt

with col3:
    if st.button("🔮 Demand Forecast", use_container_width=True):
        forecast_prompt = "Generate a demand forecast for the next quarter."
        st.session_state["quick_action_prompt"] = forecast_prompt

with col4:
    if st.button("🏆 Competitive Analysis", use_container_width=True):
        competitive_prompt = "Analyze our competitive position and recommend pricing adjustments."
        st.session_state["quick_action_prompt"] = competitive_prompt

# Handle quick action prompts
if "quick_action_prompt" in st.session_state:
    quick_prompt = st.session_state.pop("quick_action_prompt")
    st.rerun()

# Export chat history
st.markdown("---")
if st.button("📤 Export Chat History"):
    current_thread_messages = st.session_state.get("threads", {}).get(st.session_state.get("current_thread_id"), {}).get("messages", [])
    if current_thread_messages:
        chat_text = ""
        for msg in current_thread_messages:
            role = "You" if msg["role"] == "user" else "FluxPricer AI"
            chat_text += f"{role} ({msg.get('time', '')}):\n{msg['content']}\n\n"
        
        st.download_button(
            label="💾 Download Chat as Text",
            data=chat_text,
            file_name=f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    else:
        st.info("No messages to export in current chat.")