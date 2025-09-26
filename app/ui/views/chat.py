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
    
    # Add custom CSS to improve chat layout and reduce excessive spacing
    st.markdown("""
    <style>
    /* Reduce main container padding to eliminate black spaces */
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 2rem !important;
    }
    
    /* Ensure chat messages have proper spacing */
    .stChatMessage {
        margin-bottom: 0.5rem !important;
    }
    
    /* Style the chat input area */
    .stChatInput > div {
        background: white !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    import os
    if os.getenv("DEBUG_LLM", "0") == "1":
        print("[DEBUG] Entering chat view")

    agent = _get_agent()

    # Initialize chat history in session state if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if os.getenv("DEBUG_LLM", "0") == "1":
        try:
            agent_mem_len = len(getattr(agent, "memory", []))
        except Exception:
            agent_mem_len = -1
        print(f"[DEBUG] Chat state: chat_history_len={len(st.session_state.chat_history)}, agent_memory_len={agent_mem_len}")

    # Display conversation history from session state with container to control spacing
    chat_container = st.container()
    with chat_container:
        if st.session_state.chat_history:
            for msg in st.session_state.chat_history:
                role = msg.get("role")
                content = msg.get("content", "")
                if role == "user":
                    st.chat_message("user").markdown(content)
                else:
                    st.chat_message("assistant").markdown(content)
        else:
            st.info("💬 Ask me about pricing, market data, or system operations...")

    # Handle pre-filled prompts from shortcuts
    if st.session_state.get('chat_prompt'):
        prompt = st.session_state['chat_prompt']
        st.session_state['chat_prompt'] = None  # Clear after using
        if os.getenv("DEBUG_LLM", "0") == "1":
            print(f"[DEBUG] Handling prefilled chat_prompt: '{prompt[:80]}'")
        
        # Add to history and display
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.chat_message("user").markdown(prompt)
        
        # Get AI response
        reply = agent.get_response(prompt)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").markdown(reply)
        
        # Ensure dashboard URL is maintained
        st.query_params["page"] = "dashboard"
        st.query_params["section"] = "chat"
        st.rerun()
    
    # Check for quick input suggestions
    if st.session_state.get('chat_input'):
        suggested_prompt = st.session_state['chat_input']
        st.session_state['chat_input'] = None  # Clear after showing
        st.info(f"💡 Suggested: {suggested_prompt}")

    # Chat input with a stable key to avoid widget clashes
    prompt = st.chat_input("Ask about prices, rules, proposals, or market trends…", key="chat_input_main")
    if prompt:
        if os.getenv("DEBUG_LLM", "0") == "1":
            print(f"[DEBUG] Chat input received: '{prompt[:50]}...'")
            
        # Add user message to history and display immediately
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Show loading state while getting AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if os.getenv("DEBUG_LLM", "0") == "1":
                    print(f"[DEBUG] Getting AI response via agent.get_response()...")
                
                # Get AI response with robust error handling
                reply = None
                try:
                    reply = agent.get_response(prompt)
                except Exception as e:
                    if os.getenv("DEBUG_LLM", "0") == "1":
                        print(f"[DEBUG] agent.get_response raised: {e}")
                    reply = f"[non-LLM assistant] Error invoking AI: {e}"
                if reply is None or not isinstance(reply, str) or not reply.strip():
                    reply = "[non-LLM assistant] No response generated. If you intended an AI reply, try a pricing-related question or configure an API key."

            # Display the response
            st.markdown(reply)

        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        
        if os.getenv("DEBUG_LLM", "0") == "1":
            print(f"[DEBUG] Assistant reply len={len(reply)}; maintaining dashboard URL and rerunning")
            
        # Ensure dashboard URL is maintained during chat
        st.query_params["page"] = "dashboard" 
        st.query_params["section"] = "chat"
        st.rerun()
