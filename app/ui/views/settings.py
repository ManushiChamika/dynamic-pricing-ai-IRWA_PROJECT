from __future__ import annotations
import streamlit as st
import json
from app.ui.theme.inject import apply_theme
from app.ui.services import alerts as alerts_svc
from app.ui.services.runtime import run_async


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
