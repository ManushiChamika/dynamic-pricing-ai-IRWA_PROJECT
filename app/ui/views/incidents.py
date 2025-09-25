from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import Optional
from datetime import datetime, timezone

from app.ui.theme.inject import apply_theme
from app.ui.services import alerts as alerts_svc
from app.ui.services.runtime import run_async


def view() -> None:
    apply_theme(False)

    st.subheader("🔔 Incidents")
    status: Optional[str] = st.selectbox("Filter by status", ["", "OPEN", "ACKED", "RESOLVED"], index=0)
    status = status or None

    rows = run_async(alerts_svc.list_incidents(status)) or []

    top_cols = st.columns([1, 4])
    with top_cols[0]:
        if st.button("Refresh"):
            st.rerun()
    with top_cols[1]:
        if rows:
            st.dataframe(pd.DataFrame(rows))
        else:
            st.info("No incidents to display.")

    st.markdown("### Actions")
    col1, col2, col3 = st.columns(3)

    # Acknowledge controls
    with col1:
        st.caption("Acknowledge by ID or selection")
        ack_id = st.text_input("Incident ID to Ack", key="ack_id")
        if st.button("Acknowledge") and ack_id:
            res = run_async(alerts_svc.ack_incident(ack_id))
            if res and res.get("ok"):
                st.success(f"Incident {ack_id} ACKED")
            else:
                st.error(f"Failed to ack {ack_id}")
        if rows:
            selected_ack = st.selectbox(
                "Select Incident to Ack",
                options=[r["id"] for r in rows],
                key="ack_select",
            )
            if st.button("Ack Selected"):
                res = run_async(alerts_svc.ack_incident(selected_ack))
                if res and res.get("ok"):
                    st.success(f"Incident {selected_ack} ACKED")
                else:
                    st.error(f"Failed to ack {selected_ack}")

    # Resolve controls
    with col2:
        st.caption("Resolve by ID or selection")
        res_id = st.text_input("Incident ID to Resolve", key="res_id")
        if st.button("Resolve") and res_id:
            res = run_async(alerts_svc.resolve_incident(res_id))
            if res and res.get("ok"):
                st.success(f"Incident {res_id} RESOLVED")
            else:
                st.error(f"Failed to resolve {res_id}")
        if rows:
            selected_res = st.selectbox(
                "Select Incident to Resolve",
                options=[r["id"] for r in rows],
                key="res_select",
            )
            if st.button("Resolve Selected"):
                res = run_async(alerts_svc.resolve_incident(selected_res))
                if res and res.get("ok"):
                    st.success(f"Incident {selected_res} RESOLVED")
                else:
                    st.error(f"Failed to resolve {selected_res}")

    # Generators
    with col3:
        st.caption("Generate test events to exercise rules")
        sku = st.text_input("SKU", value="SKU-123", key="test_sku")

        st.write("Market Tick")
        our = st.number_input("Our Price", value=100.0, step=1.0, key="test_our")
        comp = st.number_input("Competitor Price", value=90.0, step=1.0, key="test_comp")
        demand = st.slider("Demand Index", min_value=0.0, max_value=1.0, value=0.9, step=0.05, key="test_demand")
        if st.button("Publish Test Tick"):
            try:
                from core.agents.agent_sdk import get_bus, Topic
                from types import SimpleNamespace
                bus = get_bus()
                tick = SimpleNamespace(
                    sku=sku,
                    market="DEFAULT",
                    our_price=float(our),
                    competitor_price=float(comp),
                    demand_index=float(demand),
                    ts=datetime.now(timezone.utc),
                )
                run_async(bus.publish(Topic.MARKET_TICK.value, tick))
                st.success("Published test tick. If rules match, incidents will appear.")
            except Exception as e:
                st.error(f"Failed to publish tick: {e}")

        st.write("Price Proposal")
        pp_price = st.number_input("Proposed Price", value=120.0, step=1.0, key="test_pp_price")
        pp_margin = st.number_input("Margin", value=0.25, step=0.01, key="test_pp_margin")
        if st.button("Publish Test Price Proposal"):
            try:
                from core.agents.agent_sdk import get_bus, Topic
                from types import SimpleNamespace
                bus = get_bus()
                pp = SimpleNamespace(
                    sku=sku,
                    proposed_price=float(pp_price),
                    margin=float(pp_margin),
                    ts=datetime.now(timezone.utc),
                )
                run_async(bus.publish(Topic.PRICE_PROPOSAL.value, pp))
                st.success("Published test price proposal. If rules match, incidents will appear.")
            except Exception as e:
                st.error(f"Failed to publish price proposal: {e}")
