# pricing_ui_integration.py
# Simple script to integrate pricing optimizer with UI messaging

import streamlit as st
import threading
import time
import re
from core.agents.pricing_optimizer_bus.bus_iface import bus
from core.agents.pricing_optimizer_bus.bus_events import PricingOptimizerEvents
import asyncio
from core.agents.price_optimizer.agent import PricingOptimizerAgent

def handle_pricing_request(user_input):
    """Handle pricing request with real-time status updates"""
    # Extract product name from user input
    product_match = re.search(r'for\s+(\w+)', user_input.lower())
    product_name = product_match.group(1) if product_match else "iphone15"
    
    # Initialize status tracking
    if "pricing_status" not in st.session_state:
        st.session_state["pricing_status"] = "Ready"
    
    # Set up bus listener for status updates
    def status_listener(event_data):
        if isinstance(event_data, dict) and "msg" in event_data:
            st.session_state["pricing_status"] = event_data["msg"]
    
    # Subscribe to bus events
    bus.subscribe(status_listener)
    
    # Run pricing optimizer in background thread (need to handle async)
    def run_pricing():
        try:
            agent = PricingOptimizerAgent()
            result = asyncio.run(agent.process_full_workflow(user_input, product_name))
            # Store result in session state
            st.session_state["pricing_result"] = result
            if result.get("status") == "ok":
                st.session_state["pricing_status"] = f"✅ Pricing complete for {product_name}: ${result.get('price', 'N/A')} using {result.get('algorithm', 'unknown')} algorithm"
            else:
                st.session_state["pricing_status"] = f"❌ Error: {result.get('message', 'Unknown error')}"
        except Exception as e:
            st.session_state["pricing_status"] = f"❌ Error: {str(e)}"
    
    # Start pricing in background
    threading.Thread(target=run_pricing, daemon=True).start()
    
    return f"🔄 Starting pricing analysis for {product_name}. Please wait..."

def get_pricing_status():
    """Get current pricing status for UI display"""
    return st.session_state.get("pricing_status", "Ready")

def get_pricing_result():
    """Get latest pricing result"""
    return st.session_state.get("pricing_result", None)
