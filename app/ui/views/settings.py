from __future__ import annotations
import os
import streamlit as st
import json
from app.ui.theme.inject import apply_theme
from app.ui.services import alerts as alerts_svc
from app.ui.services.runtime import run_async
try:
    from app.llm_client import get_llm_client  # optional import guard
except Exception:
    get_llm_client = None


def view() -> None:
    apply_theme(False)

    st.subheader("⚙️ Alert Channel Settings")

    settings = run_async(alerts_svc.get_settings()) or {}
    st.caption("Settings are redacted by backend where necessary (e.g., smtp_password).")

    pretty = json.dumps(settings, indent=2) if settings else "{}"
    new_text = st.text_area("Edit settings JSON", value=pretty, height=240)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Settings"):
            try:
                payload = json.loads(new_text or "{}")
            except Exception as e:
                st.error(f"Invalid JSON: {e}")
            else:
                ok = run_async(alerts_svc.save_settings(payload))
                if ok:
                    st.success("Settings saved")
                else:
                    st.error("Failed to save settings")
    with col2:
        if st.button("Reload from Server"):
            st.rerun()

    st.divider()
    st.subheader("🤖 LLM & Chat")
    st.caption("Configure keys in .env, then restart the app.")

    # Show env presence (masked)
    or_key_present = bool(os.getenv("OPENROUTER_API_KEY"))
    oa_key_present = bool(os.getenv("OPENAI_API_KEY"))
    gem_key_present = bool(os.getenv("GEMINI_API_KEY"))
    st.write(
        " · ".join(
            [
                f"OPENROUTER_API_KEY: {'present' if or_key_present else 'missing'}",
                f"OPENAI_API_KEY: {'present' if oa_key_present else 'missing'}",
                f"GEMINI_API_KEY: {'present' if gem_key_present else 'missing'}",
            ]
        )
    )

    provider = model = status = reason = None
    if get_llm_client is not None:
        llm = get_llm_client()
        provider = llm.provider()
        model = getattr(llm, 'model', None)
        available = llm.is_available()
        if available:
            status = "available"
        else:
            status = "unavailable"
            reason = llm.unavailable_reason() or "unknown"
        cols = st.columns(3)
        cols[0].metric("Provider", provider or "none")
        cols[1].metric("Model", model or "<auto>")
        cols[2].metric("Status", status)
        st.caption("Fallback order: OpenRouter → OpenAI → Gemini (if configured).")
        if reason and status != "available":
            st.info(f"LLM unavailable: {reason}")

        test_prompt = st.text_input("Quick test prompt", value="Say 'OK' only.")
        if st.button("Test LLM"):
            if not available:
                st.error("LLM client is unavailable. Set API keys and restart.")
            else:
                try:
                    answer = llm.chat([
                        {"role": "system", "content": "You are a concise test helper."},
                        {"role": "user", "content": test_prompt},
                    ], max_tokens=16, temperature=0.0)
                    st.success("LLM responded:")
                    st.code(answer)
                except Exception as e:
                    st.error(f"LLM test failed: {e}")
    else:
        st.warning("LLM client not importable; check app.llm_client.py and dependencies.")

