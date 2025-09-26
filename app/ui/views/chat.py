from __future__ import annotations
import os
import streamlit as st
from app.ui.theme.inject import apply_theme
from pathlib import Path
from core.agents.user_interact.user_interaction_agent import UserInteractionAgent


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


def view() -> None:
    apply_theme(False)
    _ensure_state()

    # Minimal layout: rely on native Streamlit chat components
    st.markdown(
        """
        <style>
        .main .block-container {
            padding-top: 0.25rem !important;
            padding-bottom: 0.25rem !important;
            background: linear-gradient(180deg, #F8FAFC 0%, #EEF2FF 100%) !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) inset;
        }
        
        /* Aesthetic polish for chat messages */
        [data-testid="stChatMessage"] { padding: 0.25rem 0 !important; }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 12px !important;
            padding: 0.6rem 0.85rem !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05) !important;
            display: inline-block !important;
            max-width: 75% !important;
        }
        /* Align by role using :has() when available (progressive enhancement) */
        [data-testid="stChatMessage"]:has(svg[data-testid="user-avatar-icon"]) [data-testid="stMarkdownContainer"] {
            background: #F1F5F9 !important;
            border-color: #CBD5E1 !important;
            margin-left: auto !important;
        }
        [data-testid="stChatMessage"]:has(svg[data-testid="assistant-avatar-icon"]) [data-testid="stMarkdownContainer"] {
            background: #FFFFFF !important;
            border-color: #E2E8F0 !important;
            margin-right: auto !important;
        }
        /* Markdown content polish inside bubbles */
        [data-testid="stMarkdownContainer"] p { margin: 0.25rem 0 0.35rem 0 !important; }
        [data-testid="stMarkdownContainer"] ul { margin: 0.25rem 0 0.35rem 1.25rem !important; }
        [data-testid="stMarkdownContainer"] code {
            background: #F8FAFC !important;
            border: 1px solid #E2E8F0 !important;
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
            background: linear-gradient(135deg, #EFF6FF 0%, #EEF2FF 100%);
            border: 1px solid #BFDBFE;
            color: #1E3A8A;
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
            background: linear-gradient(135deg, #3B82F6, #1D4ED8);
            animation: typing-bounce 1.2s infinite ease-in-out;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.15s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.3s; }
        @keyframes typing-bounce {
            0%, 80%, 100% { transform: translateY(0); opacity: 0.6; }
            40% { transform: translateY(-4px); opacity: 1; }
        }
        .typing-text { font-weight: 600; font-size: 0.9rem; }

        /* Avatar polish - subtle ring */
        [data-testid="stChatMessage"] img[alt*="avatar"],
        [data-testid="stChatMessage"] svg[data-testid$="avatar-icon"] {
            box-shadow: 0 0 0 3px #FFFFFF, 0 0 0 5px #DBEAFE;
            border-radius: 50%;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    agent = _get_agent()

    # Avatars
    assets_dir = Path(__file__).resolve().parents[3] / "assets"
    assistant_avatar_path = assets_dir / "robo.png"
    assistant_avatar = str(assistant_avatar_path) if assistant_avatar_path.exists() else "🤖"
    user_avatar = "🧑‍💼"

    # Auto-send prefilled prompt from dashboard shortcuts
    prefill = st.session_state.pop("chat_prompt", None)
    if prefill and isinstance(prefill, str) and prefill.strip():
        st.session_state.chat_history.append({"role": "user", "content": prefill.strip()})
        st.session_state["awaiting"] = prefill.strip()
        st.query_params["page"] = "dashboard"
        st.query_params["section"] = "chat"
        st.rerun()

    # Render history
    for msg in st.session_state.chat_history:
        role = msg.get("role", "assistant")
        content = str(msg.get("content") or "")
        with st.chat_message("user" if role == "user" else "assistant", avatar=(user_avatar if role == "user" else assistant_avatar)):
            st.markdown(content)

    # If awaiting a reply, fetch it and render spinner inline
    awaiting = st.session_state.get("awaiting")
    if awaiting:
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
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.session_state["awaiting"] = ""
        st.query_params["page"] = "dashboard"
        st.query_params["section"] = "chat"
        st.rerun()

    # Chat input (Enter to send)
    prompt = st.chat_input("Ask about prices, rules, proposals, or market trends…")
    if prompt and prompt.strip():
        st.session_state.chat_history.append({"role": "user", "content": prompt.strip()})
        st.session_state["awaiting"] = prompt.strip()
        st.query_params["page"] = "dashboard"
        st.query_params["section"] = "chat"
        st.rerun()