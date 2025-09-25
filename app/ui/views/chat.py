from __future__ import annotations
import streamlit as st
from app.ui.theme.inject import apply_theme
from core.agents.user_interact.user_interaction_agent import UserInteractionAgent


def _get_agent() -> UserInteractionAgent:
    user = (st.session_state.get("session") or {}).get("full_name") or "User"
    if "_chat_agent" not in st.session_state:
        st.session_state["_chat_agent"] = UserInteractionAgent(user_name=user)
    return st.session_state["_chat_agent"]


def view() -> None:
    apply_theme(False)

    st.subheader("💬 Chat")
    agent = _get_agent()

    # Display conversation history
    history = getattr(agent, "memory", [])
    if history:
        for msg in history:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                st.chat_message("user").markdown(content)
            else:
                st.chat_message("assistant").markdown(content)
    else:
        st.info("Start a conversation about dynamic pricing, proposals, rules, or market data.")

    # Handle pre-filled prompts from shortcuts
    if st.session_state.get('chat_prompt'):
        prompt = st.session_state['chat_prompt']
        st.session_state['chat_prompt'] = None  # Clear after using
        st.chat_message("user").markdown(prompt)
        reply = agent.get_response(prompt)
        st.chat_message("assistant").markdown(reply)
    
    # Check for quick input suggestions
    if st.session_state.get('chat_input'):
        suggested_prompt = st.session_state['chat_input']
        st.session_state['chat_input'] = None  # Clear after showing
        st.info(f"💡 Suggested: {suggested_prompt}")

    # Chat input
    prompt = st.chat_input("Ask about prices, rules, proposals, or market trends…")
    if prompt:
        st.chat_message("user").markdown(prompt)
        reply = agent.get_response(prompt)
        st.chat_message("assistant").markdown(reply)
