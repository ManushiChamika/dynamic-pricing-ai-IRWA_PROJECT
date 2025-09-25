from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import Any, Dict

from app.ui.theme.inject import apply_theme
from app.ui.services import alerts as alerts_svc
from app.ui.services.runtime import run_async


def _bool(v: Any) -> bool:
    return bool(v) if v is not None else False


def view() -> None:
    apply_theme(False)

    st.subheader("🧩 Rules")

    # List current rules
    cols = st.columns([4, 1])
    with cols[0]:
        rows = run_async(alerts_svc.list_rules()) or []
        if rows:
            st.dataframe(pd.DataFrame(rows))
        else:
            st.info("No rules yet.")
    with cols[1]:
        if st.button("Reload Rules"):
            ok = run_async(alerts_svc.reload_rules())
            if ok:
                st.success("Reloaded rules in engine")
            else:
                st.error("Failed to reload rules")

    st.markdown("---")
    st.markdown("### Create Rule")

    with st.form("create_rule_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            rule_id = st.text_input("ID", placeholder="unique-rule-id")
        with c2:
            source = st.selectbox("Source", ["MARKET_TICK", "PRICE_PROPOSAL"], index=0)
        with c3:
            severity = st.selectbox("Severity", ["info", "warn", "crit"], index=1)

        c4, c5 = st.columns(2)
        with c4:
            where = st.text_area("Where (expression)", placeholder="demand_index < 0.2 and competitor_price < our_price")
        with c5:
            detector = st.text_input("Detector (name)", placeholder="spike_detector")

        field = st.text_input("Field (optional)", value="")
        hold_for = st.text_input("Hold For (e.g., 5m)", value="")
        dedupe = st.text_input("Dedupe", value="sku")
        group_by_text = st.text_input("Group By (comma separated)", value="")
        enabled = st.checkbox("Enabled", value=True)

        st.caption("Notification channels (UI, Slack, Email, Webhook)")
        channels = st.multiselect("Channels", ["ui", "slack", "email", "webhook"], default=["ui"])
        throttle = st.text_input("Throttle (e.g., 15m)", value="")
        webhook_url = st.text_input("Webhook URL", value="")
        email_to_text = st.text_input("Email To (comma separated)", value="")

        submitted = st.form_submit_button("Create Rule")

    if submitted:
        if not rule_id:
            st.error("Rule ID is required.")
            return
        if (where and detector) or (not where and not detector):
            st.error("Provide either 'where' OR 'detector', but not both.")
            return

        group_by = [x.strip() for x in group_by_text.split(",") if x.strip()] if group_by_text else []
        email_to = [x.strip() for x in email_to_text.split(",") if x.strip()] if email_to_text else None

        spec: Dict[str, Any] = {
            "id": rule_id,
            "source": source,
            "where": where or None,
            "detector": detector or None,
            "field": field or None,
            "params": {},
            "hold_for": hold_for or None,
            "severity": severity,
            "dedupe": dedupe or "sku",
            "group_by": group_by,
            "notify": {
                "channels": channels or ["ui"],
                "throttle": throttle or None,
                "webhook_url": webhook_url or None,
                "email_to": email_to,
            },
            "enabled": _bool(enabled),
        }

        res = run_async(alerts_svc.create_rule(spec))
        if res and res.get("ok"):
            st.success(f"Rule '{rule_id}' created.")
            st.rerun()
        else:
            st.error(f"Failed to create rule: {res}")
