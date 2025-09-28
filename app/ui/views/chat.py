from __future__ import annotations
import streamlit as st
from pathlib import Path
from app.ui.theme.inject import apply_theme
from app.ui.state.session import current_user
from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
from app.ui.services import chat_threads as ct


def _check_if_requires_poa(message: str) -> bool:
    """Check if a message requires Price Optimization Agent."""
    message_lower = message.lower()
    
    # Complex pricing keywords that suggest POA is needed
    poa_keywords = [
        "optimize price", "pricing strategy", "maximize profit", "competitive pricing",
        "market analysis", "algorithm", "ml model", "profit maximization", 
        "rule based", "competitor price", "pricing workflow", "complex pricing",
        "advanced pricing", "ai pricing", "intelligent pricing"
    ]
    
    # Simple queries that UIA can handle alone
    simple_keywords = [
        "current price", "list products", "show inventory", "what is the price",
        "price of", "cost of", "how much", "market price", "proposals"
    ]
    
    # Check if it's a simple query first
    if any(keyword in message_lower for keyword in simple_keywords):
        # But if it also has complex keywords, it still needs POA
        if any(keyword in message_lower for keyword in poa_keywords):
            return True
        return False
    
    # Check for complex pricing needs
    return any(keyword in message_lower for keyword in poa_keywords)


def _check_if_triggers_dca(message: str) -> bool:
    """Heuristic to detect if message likely triggers Data Collection Agent (collect_market_data)."""
    m = message.lower()
    dca_keywords = [
        "collect market data", "collect data", "data collection", "gather data", "refresh data",
        "update market", "fetch market", "scrape", "web scraper", "competitor data",
        "ingest data", "pull latest data", "update pricing data"
    ]
    return any(k in m for k in dca_keywords)


def _check_if_triggers_ana(message: str) -> bool:
    """Heuristic to detect if message likely triggers Alert & Notification Agent (scan_for_alerts)."""
    m = message.lower()
    ana_keywords = [
        "alerts", "scan alerts", "check alerts", "critical", "anomaly", "anomalies",
        "margin breach", "breach", "undercut", "competitor undercut", "risk", "monitor",
        "scan for", "situations", "issues", "problems", "warning", "incident"
    ]
    return any(k in m for k in ana_keywords)


def _get_agent() -> UserInteractionAgent:
    user = (st.session_state.get("session") or {}).get("full_name") or "User"
    if "_chat_agent" not in st.session_state:
        st.session_state["_chat_agent"] = UserInteractionAgent(user_name=user)
    return st.session_state["_chat_agent"]


def _ensure_state() -> None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "_pending_prompt" not in st.session_state:
        st.session_state._pending_prompt = ""
    if "awaiting" not in st.session_state:
        st.session_state["awaiting"] = ""
    if "_waiting_for_response" not in st.session_state:
        st.session_state._waiting_for_response = False


def _ensure_thread_initialized() -> str:
    user = current_user()
    
    # Debug logging
    import os
    debug = os.getenv("DEBUG_LLM", "0") == "1"
    if debug:
        print(f"[DEBUG] _ensure_thread_initialized - URL: {st.query_params.get('thread')}, Session: {st.session_state.get('current_thread_id')}")
    
    # Always prefer URL param when present and valid
    tid = st.query_params.get("thread")
    if tid and ct.thread_exists(user, tid):
        if debug:
            print(f"[DEBUG] Using URL thread: {tid}")
        st.session_state["current_thread_id"] = tid
        return tid

    # Fallback to session value if valid
    session_tid = st.session_state.get("current_thread_id")
    if session_tid and ct.thread_exists(user, session_tid):
        if debug:
            print(f"[DEBUG] Using session thread: {session_tid}")
        # Update URL to match session state
        st.query_params["thread"] = session_tid
        return session_tid

    # Otherwise, pick the most recent existing thread or create one
    first = ct.first_thread_id(user)
    if first:
        if debug:
            print(f"[DEBUG] Using first available thread: {first}")
        st.session_state["current_thread_id"] = first
        st.query_params["thread"] = first
        return first

    new_tid = ct.create_thread(user, title="New chat")
    if debug:
        print(f"[DEBUG] Created new thread: {new_tid}")
    st.session_state["current_thread_id"] = new_tid
    st.query_params["thread"] = new_tid
    return new_tid


def _migrate_legacy_history_to_thread(tid: str) -> None:
    # If any old session chat_history exists, move it once into a new thread
    if st.session_state.get("chat_history"):
        user = current_user()
        imported_tid = ct.create_thread(user, title="Imported chat")
        for m in st.session_state.chat_history:
            role = m.get("role", "assistant")
            content = str(m.get("content") or "")
            if content:
                ct.append_message(user, imported_tid, role, content)
        st.session_state.chat_history = []
        st.session_state["current_thread_id"] = imported_tid
        st.query_params["thread"] = imported_tid


def view() -> None:
    apply_theme(None)
    _ensure_state()

    # Minimal layout: rely on native Streamlit chat components
    st.markdown(
        """
        <style>
        .main .block-container { padding-top: 0.25rem !important; padding-bottom: 0.25rem !important; }
        
        /* Aesthetic polish for chat messages */
        [data-testid="stChatMessage"] { padding: 0.25rem 0 !important; }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
            background: var(--bubble-assistant-bg, var(--bubble-assistant-bg-light)) !important;
            border: 1px solid var(--bubble-assistant-border, var(--bubble-assistant-border-light)) !important;
            border-radius: 12px !important;
            padding: 0.6rem 0.85rem !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05) !important;
            display: inline-block !important;
            max-width: 75% !important;
            color: var(--bubble-fg, #111827) !important;
        }
        /* Align by role using :has() when available (progressive enhancement) */
        [data-testid="stChatMessage"]:has(svg[data-testid="user-avatar-icon"]) [data-testid="stMarkdownContainer"] {
            background: var(--bubble-user-bg, var(--bubble-user-bg-light)) !important;
            border-color: var(--bubble-user-border, var(--bubble-user-border-light)) !important;
            margin-left: auto !important;
            color: var(--bubble-fg, #111827) !important;
        }
        [data-testid="stChatMessage"]:has(svg[data-testid="assistant-avatar-icon"]) [data-testid="stMarkdownContainer"] {
            background: var(--bubble-assistant-bg, var(--bubble-assistant-bg-light)) !important;
            border-color: var(--bubble-assistant-border, var(--bubble-assistant-border-light)) !important;
            margin-right: auto !important;
            color: var(--bubble-fg, #111827) !important;
        }
        /* Markdown content polish inside bubbles */
        [data-testid="stMarkdownContainer"] p { margin: 0.25rem 0 0.35rem 0 !important; }
        [data-testid="stMarkdownContainer"] ul { margin: 0.25rem 0 0.35rem 1.25rem !important; }
        [data-testid="stMarkdownContainer"] code {
            background: rgba(148, 163, 184, 0.15) !important;
            border: 1px solid rgba(148, 163, 184, 0.35) !important;
            border-radius: 6px !important;
            padding: 0.1rem 0.35rem !important;
        }
        [data-testid="stMarkdownContainer"] pre code {
            background: #0F172A !important;
            color: #E2E8F0 !important;
            border-radius: 10px !important;
            padding: 0.75rem 1rem !important;
            border: 1px solid #1F2937 !important;
            box-shadow: inset 0 0 0 1px rgba(255,255,255,0.04);
        }

        /* Typing bubble */
        .typing-bubble {
            background: var(--typing-bg, linear-gradient(135deg, #EFF6FF 0%, #EEF2FF 100%));
            border: 1px solid var(--typing-border, #BFDBFE);
            color: var(--typing-fg, #1E3A8A);
            border-radius: 12px;
            padding: 0.5rem 0.75rem;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        }
        .typing-dots { display: inline-flex; gap: 0.25rem; }
        .typing-dots span {
            width: 6px; height: 6px; border-radius: 50%; display: inline-block;
            background: linear-gradient(135deg, var(--typing-dot-start, #3B82F6), var(--typing-dot-end, #1D4ED8));
            animation: typing-bounce 1.2s infinite ease-in-out;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.15s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.3s; }
        @keyframes typing-bounce {
            0%, 80%, 100% { transform: translateY(0); opacity: 0.6; }
            40% { transform: translateY(-4px); opacity: 1; }
        }
        .typing-text { font-weight: 600; font-size: 0.9rem; }

        /* Avatar: use minimal 2D monochrome look via emoji fallback; remove ring */
        [data-testid="stChatMessage"] img[alt*="avatar"],
        [data-testid="stChatMessage"] svg[data-testid$="avatar-icon"] { box-shadow: none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    agent = _get_agent()

    # Avatars (emoji-based)
    assistant_avatar = "✨"
    user_avatar = "👤"

    # Ensure a thread exists and migrate any legacy session history
    tid = _ensure_thread_initialized()
    _migrate_legacy_history_to_thread(tid)
    
    # Debug: log current thread state
    import os
    if os.getenv("DEBUG_LLM", "0") == "1":
        print(f"[DEBUG] Chat view - Current thread: {tid}, Session thread: {st.session_state.get('current_thread_id')}, URL thread: {st.query_params.get('thread')}")

    # Header with click-to-rename title (no persistent text input)
    user = current_user()
    meta = ct.get_thread(user, tid) or {"title": "Chat"}
    toast_info = st.session_state.pop("_toast_llm_renamed", None)
    if toast_info and toast_info.get("tid") == tid:
        try:
            st.toast(f"Chat renamed to \"{toast_info.get('title')}\"")
        except Exception:
            st.info(f"Chat renamed to \"{toast_info.get('title')}\"")
    st.markdown("<div style=\"max-width: 820px; margin: 0 auto;\">", unsafe_allow_html=True)
    edit_key = f"_editing_title_{tid}"
    if st.session_state.get(edit_key):
        c1, c2 = st.columns([0.8, 0.2])
        with c1:
            new_title = st.text_input("Rename chat", value=meta.get("title") or "Untitled", key=f"title_input_{tid}")
        with c2:
            save = st.button("Save", key=f"save_title_{tid}", use_container_width=True)
        cancel = st.button("Cancel", key=f"cancel_title_{tid}")
        if save:
            ct.rename_thread(user, tid, new_title, by="user")
            st.session_state[edit_key] = False
            st.rerun()
        elif cancel:
            st.session_state[edit_key] = False
            st.rerun()
    else:
        title_display = meta.get("title") or "Untitled"
        # Make the title itself a button (styled as plain header) to enter edit mode
        st.markdown(f"""
        <style>
        button[key=\"title_click_{tid}\"] {{
            background: transparent !important;
            border: none !important;
            padding: 0 !important;
            text-align: left !important;
            font-size: 1.5rem !important; /* ~h3 */
            font-weight: 700 !important;
            color: inherit !important;
        }}
        button[key=\"title_click_{tid}\"]:hover {{
            text-decoration: underline;
            cursor: pointer;
        }}
        </style>
        """, unsafe_allow_html=True)
        if st.button(title_display, key=f"title_click_{tid}"):
            st.session_state[edit_key] = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # Auto-send prefilled prompt from dashboard shortcuts
    prefill = st.session_state.pop("chat_prompt", None)
    if prefill and isinstance(prefill, str) and prefill.strip():
        ct.append_message(current_user(), tid, "user", prefill.strip())
        st.session_state["awaiting"] = prefill.strip()
        st.query_params["page"] = "dashboard"
        st.query_params["section"] = "chat"
        st.query_params["thread"] = tid
        st.rerun()

    # Render history - centered narrower column
    st.markdown("<div style=\"max-width: 820px; margin: 0 auto;\">", unsafe_allow_html=True)
    msgs = ct.load_messages(current_user(), tid)
    for msg in msgs:
        role = msg.get("role", "assistant")
        content = str(msg.get("content") or "")
        with st.chat_message("user" if role == "user" else "assistant", avatar=(user_avatar if role == "user" else assistant_avatar)):
            st.markdown(content)

    # If awaiting a reply, fetch it and render spinner inline
    awaiting = st.session_state.get("awaiting")
    if awaiting:
        # Rehydrate agent memory from persisted thread so LLM sees history across reloads
        try:
            _hist = ct.load_messages(current_user(), tid)
            agent.memory = [{"role": m.get("role", "user"), "content": str(m.get("content") or "")} for m in _hist if str(m.get("content") or "").strip()]
        except Exception:
            agent.memory = []
        with st.chat_message("assistant", avatar=assistant_avatar):
            ph = st.empty()
            ph.markdown(
                """
                <div class="typing-bubble">
                    <div class="typing-dots"><span></span><span></span><span></span></div>
                    <div class="typing-text">Thinking…</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Show staged feedback depending on detected intent
            requires_poa = _check_if_requires_poa(awaiting)
            triggers_ana = _check_if_triggers_ana(awaiting)
            triggers_dca = _check_if_triggers_dca(awaiting)
            if requires_poa:
                # Show enhanced POA status with multiple stages
                import time
                
                # Stage 1: Analyzing request
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); border-color: #F59E0B; color: #92400E;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #F59E0B, #D97706);"></span><span style="background: linear-gradient(135deg, #F59E0B, #D97706);"></span><span style="background: linear-gradient(135deg, #F59E0B, #D97706);"></span></div>
                        <div class="typing-text">🤖 Price Optimization Agent: Analyzing request...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(1)
                
                # Stage 2: AI algorithm selection
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%); border-color: #3B82F6; color: #1D4ED8;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #3B82F6, #1D4ED8);"></span><span style="background: linear-gradient(135deg, #3B82F6, #1D4ED8);"></span><span style="background: linear-gradient(135deg, #3B82F6, #1D4ED8);"></span></div>
                        <div class="typing-text">🧠 AI Brain: Selecting optimal algorithm...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(1)
                
                # Stage 3: Market analysis
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #DCFCE7 0%, #BBF7D0 100%); border-color: #10B981; color: #047857;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #10B981, #047857);"></span><span style="background: linear-gradient(135deg, #10B981, #047857);"></span><span style="background: linear-gradient(135deg, #10B981, #047857);"></span></div>
                        <div class="typing-text">📊 Market Analysis: Processing competitive data...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(1)
                
                # Stage 4: Executing optimization
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #FDF2F8 0%, #FCE7F3 100%); border-color: #EC4899; color: #BE185D;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #EC4899, #BE185D);"></span><span style="background: linear-gradient(135deg, #EC4899, #BE185D);"></span><span style="background: linear-gradient(135deg, #EC4899, #BE185D);"></span></div>
                        <div class="typing-text">⚡ Executing pricing optimization...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif triggers_dca:
                import time
                # DCA staged feedback
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #E0E7FF 0%, #C7D2FE 100%); border-color: #6366F1; color: #3730A3;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #6366F1, #3730A3);"></span><span style="background: linear-gradient(135deg, #6366F1, #3730A3);"></span><span style="background: linear-gradient(135deg, #6366F1, #3730A3);"></span></div>
                        <div class="typing-text">🗂️ Data Collection: Planning sources...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(0.9)
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #F0FDFA 0%, #CCFBF1 100%); border-color: #14B8A6; color: #0F766E;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #14B8A6, #0F766E);"></span><span style="background: linear-gradient(135deg, #14B8A6, #0F766E);"></span><span style="background: linear-gradient(135deg, #14B8A6, #0F766E);"></span></div>
                        <div class="typing-text">🔌 Connecting to data sources...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(0.9)
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #FAF5FF 0%, #E9D5FF 100%); border-color: #A855F7; color: #6B21A8;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #A855F7, #6B21A8);"></span><span style="background: linear-gradient(135deg, #A855F7, #6B21A8);"></span><span style="background: linear-gradient(135deg, #A855F7, #6B21A8);"></span></div>
                        <div class="typing-text">📥 Ingesting and normalizing market data...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(0.9)
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #FFF7ED 0%, #FED7AA 100%); border-color: #F97316; color: #9A3412;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #F97316, #9A3412);"></span><span style="background: linear-gradient(135deg, #F97316, #9A3412);"></span><span style="background: linear-gradient(135deg, #F97316, #9A3412);"></span></div>
                        <div class="typing-text">📊 Updating insights and dashboard...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            elif triggers_ana:
                import time
                # ANA staged feedback
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #FDE68A 0%, #FCA5A5 100%); border-color: #F59E0B; color: #7C2D12;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #F59E0B, #B45309);"></span><span style="background: linear-gradient(135deg, #F59E0B, #B45309);"></span><span style="background: linear-gradient(135deg, #F59E0B, #B45309);"></span></div>
                        <div class="typing-text">🛡️ Alert Scanner: Loading detection rules...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(0.9)
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #E5E7EB 0%, #D1D5DB 100%); border-color: #6B7280; color: #374151;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #6B7280, #374151);"></span><span style="background: linear-gradient(135deg, #6B7280, #374151);"></span><span style="background: linear-gradient(135deg, #6B7280, #374151);"></span></div>
                        <div class="typing-text">🔍 Scanning recent pricing and market signals...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(0.9)
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%); border-color: #0EA5E9; color: #075985;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #0EA5E9, #075985);"></span><span style="background: linear-gradient(135deg, #0EA5E9, #075985);"></span><span style="background: linear-gradient(135deg, #0EA5E9, #075985);"></span></div>
                        <div class="typing-text">⚖️ Evaluating severity and impact...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                time.sleep(0.9)
                ph.markdown(
                    """
                    <div class="typing-bubble" style="background: linear-gradient(135deg, #ECFCCB 0%, #D9F99D 100%); border-color: #84CC16; color: #3F6212;">
                        <div class="typing-dots"><span style="background: linear-gradient(135deg, #84CC16, #3F6212);"></span><span style="background: linear-gradient(135deg, #84CC16, #3F6212);"></span><span style="background: linear-gradient(135deg, #84CC16, #3F6212);"></span></div>
                        <div class="typing-text">📣 Compiling alerts and recommendations...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            
            try:
                reply = agent.get_response(awaiting)
            except Exception as e:
                reply = f"[non-LLM assistant] Error invoking AI: {e}"
            ph.empty()
        if not isinstance(reply, str) or not reply.strip():
            reply = (
                "[non-LLM assistant] No response generated. If you intended an AI reply, "
                "try a pricing-related question or configure an API key."
            )
        ct.append_message(current_user(), tid, "assistant", reply)
        # After assistant reply, trigger LLM title rename if eligible
        try:
            if ct.should_llm_rename(current_user(), tid):
                from app.llm_client import get_llm_client
                llm = get_llm_client()
                if llm.is_available():
                    convo = ct.load_messages(current_user(), tid)
                    # Build a compact transcript (cap length)
                    parts = []
                    for m in convo[-12:]:
                        r = m.get("role", "user")
                        c = str(m.get("content") or "")
                        parts.append(f"{r}: {c}")
                    transcript = "\n".join(parts)
                    prompt = (
                        "You are titling a conversation. Given the transcript, return a concise 3-6 word title capturing the main topic. "
                        "No punctuation at end, no quotes, no emojis. Title-case where natural.\n\n" + transcript
                    )
                    title = llm.chat([
                        {"role": "system", "content": "Return only the title without any extra text."},
                        {"role": "user", "content": prompt},
                    ], max_tokens=32, temperature=0.2)
                    title = (title or "").strip().strip('"')
                    if title:
                        ct.rename_thread(current_user(), tid, title, by="llm")
                        st.session_state["_toast_llm_renamed"] = {"tid": tid, "title": title}
        except Exception:
            pass

        st.session_state["awaiting"] = ""
        st.query_params["page"] = "dashboard"
        st.query_params["section"] = "chat"
        st.query_params["thread"] = tid
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Chat input (Enter to send)
    st.markdown(
        """
        <style>
        [data-testid="stChatInput"] { background: transparent !important; border: none !important; }
        [data-testid="stChatInput"] > div { max-width: 820px; margin: 0.5rem auto !important; }
        [data-testid="stChatInput"] textarea, [data-testid="stChatInput"] div[contenteditable="true"] {
            min-height: 76px !important; font-size: 1rem !important;
        }
        [data-testid="stChatInput"] button { font-weight: 700 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    prompt = st.chat_input("Ask about prices, rules, proposals, or market trends…")
    if prompt and prompt.strip():
        # Ensure we're using the current thread (re-check in case it changed)
        current_tid = _ensure_thread_initialized()
        ct.append_message(current_user(), current_tid, "user", prompt.strip())
        st.session_state["awaiting"] = prompt.strip()
        st.query_params["page"] = "dashboard"
        st.query_params["section"] = "chat"
        st.query_params["thread"] = current_tid
        st.rerun()
