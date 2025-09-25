from __future__ import annotations
import streamlit as st
from app.ui.theme.inject import apply_theme
from app.ui.services.activity import recent


def view() -> None:
    apply_theme(False)

    st.subheader("🔎 Activity Feed")

    limit = st.slider("Items", min_value=10, max_value=200, value=50, step=10)
    items = recent(limit)

    if not items:
        st.info("No activity yet.")
        return

    for ev in items:
        status = ev.get("status", "info")
        badge = "🟢" if status == "completed" else ("🟡" if status == "in_progress" else ("🔴" if status == "failed" else "🔵"))
        st.markdown(f"{badge} [{ev.get('ts')}] **{ev.get('agent')}** — {ev.get('action')}")
        msg = ev.get("message")
        if msg:
            st.caption(msg)
        details = ev.get("details")
        if details:
            with st.expander("Details"):
                st.json(details)
