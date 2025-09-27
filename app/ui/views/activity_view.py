from __future__ import annotations
import streamlit as st
from app.ui.theme.inject import apply_theme
from app.ui.services.activity import recent




def view() -> None:
    apply_theme(False)

    st.subheader("🔎 Activity Feed")

    # Quick generators to ensure you can see activity immediately
    with st.expander("Generate sample activity"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Log sample activity", key="act_sample_log"):
                try:
                    from core.agents.agent_sdk.activity_log import activity_log
                    activity_log.log(agent="UI", action="sample", status="completed", message="Sample activity from button", details={"source": "activity_view"})
                    st.success("Logged sample activity")
                except Exception as e:
                    st.error(f"Failed to log sample: {e}")
        with col2:
            if st.button("Publish alert event", key="act_sample_alert"):
                try:
                    from core.agents.agent_sdk import get_bus, Topic
                    bus = get_bus()
                    # Use a simple dict payload; bridge handles dicts
                    payload = {"severity": "info", "title": "Sample alert", "sku": "TEST-1"}
                    from app.ui.services.runtime import run_async
                    run_async(bus.publish(Topic.ALERT.value, payload))
                    st.success("Published alert event")
                except Exception as e:
                    st.error(f"Failed to publish alert: {e}")

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

