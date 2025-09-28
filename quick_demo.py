#!/usr/bin/env python3
"""
Quick Demo Setup for IRWA Viva - Multi-Agent System
==================================================

This script provides a quick demonstration setup for the multi-agent system
with minimal dependencies for the viva presentation.
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def quick_setup():
    """Quick setup for demo with minimal requirements."""
    print(">> FluxPricer AI - Quick Demo Setup")
    print("=" * 50)
    
    # Set basic environment variables
    os.environ.setdefault("DEBUG_LLM", "1")
    os.environ.setdefault("SOUND_NOTIFICATIONS", "0")  # Disable for demo
    os.environ.setdefault("UI_REQUIRE_LOGIN", "0")
    os.environ.setdefault("STRICT_AI_SELECTION", "false")
    
    print("[OK] Environment configured")
    
    # Ensure demo data exists
    market_db = Path("data/market.db")
    if not market_db.exists():
        print("[INFO] Populating demo data...")
        try:
            import subprocess
            subprocess.run([sys.executable, "scripts/populate_sri_lanka_laptop_store.py"], 
                         check=True, capture_output=True)
            print("[OK] Demo data populated")
        except Exception as e:
            print(f"[WARN] Demo data setup issue: {e}")
    else:
        print("[OK] Demo data already available")
    
    return True

def demo_architecture():
    """Show the multi-agent architecture."""
    print("\n>> MULTI-AGENT ARCHITECTURE")
    print("=" * 50)
    print("┌─────────────────────────────────────────────────┐")
    print("│                 USER INPUT                      │")
    print("└─────────────────┬───────────────────────────────┘")
    print("                  │")
    print("┌─────────────────▼───────────────────────────────┐")
    print("│        UserInteractionAgent (UIA)              │")
    print("│  • Processes user queries                       │")
    print("│  • Delegates complex tasks                      │")
    print("│  • Uses built-in tools for simple queries      │")
    print("└─────────────────┬───────────────────────────────┘")
    print("                  │ run_pricing_workflow")
    print("┌─────────────────▼───────────────────────────────┐")
    print("│      PricingOptimizerAgent (POA)                │")
    print("│  • AI-driven algorithm selection               │")
    print("│  • Market data analysis                        │")
    print("│  • Publishes typed price proposals             │")
    print("└─────────────────┬───────────────────────────────┘")
    print("                  │ price.proposal events")
    print("┌─────────────────▼───────────────────────────────┐")
    print("│          Activity Monitor & UI                 │")
    print("│  • Real-time agent interaction display         │")
    print("│  • Event-driven activity feed                  │")
    print("│  • Multi-agent workflow visualization          │")
    print("└─────────────────────────────────────────────────┘")

def demo_scenarios():
    """Show demo scenarios without running code."""
    print("\n>> DEMO SCENARIOS")
    print("=" * 50)
    
    print("[SCENARIO 1] Simple Query")
    print("   User: 'What laptops do we have under LKR 100,000?'")
    print("   -> UIA handles independently with list_inventory tool")
    print("   -> Direct database query and response")
    print("   -> No agent delegation needed")
    
    print("\n[SCENARIO 2] Complex Optimization")
    print("   User: 'Optimize HP Pavilion pricing for maximum profit'")
    print("   -> UIA recognizes complex pricing task")
    print("   -> UIA calls run_pricing_workflow tool")
    print("   -> POA performs AI-driven algorithm selection")
    print("   -> POA analyzes market data and context")
    print("   -> POA publishes typed price.proposal event")
    print("   -> Activity feed shows inter-agent communication")

def demo_ai_features():
    """Show AI-driven features."""
    print("\n🧠 AI-DRIVEN FEATURES")
    print("=" * 50)
    
    print("🔍 Algorithm Selection (POA):")
    print("   • rule_based: Conservative competitive pricing (2% discount)")
    print("   • ml_model: Machine learning demand-aware pricing")
    print("   • profit_maximization: Aggressive profit-focused (10% markup)")
    
    print("\n🤖 LLM Decision Process:")
    print("   1. Analyzes user intent: 'maximize profit' → profit_maximization")
    print("   2. Considers market context: competitor prices, data freshness")
    print("   3. Selects optimal algorithm with reasoning")
    print("   4. Returns structured JSON with tool_name and rationale")
    
    print("\n📊 Market Context Analysis:")
    print("   • Record count: How much competitor data available")
    print("   • Latest price: Most recent competitor pricing")
    print("   • Average price: Market pricing baseline")
    print("   • Data freshness: When data was last updated")

def demo_event_system():
    """Show event-driven communication."""
    print("\n📡 EVENT-DRIVEN COMMUNICATION")
    print("=" * 50)
    
    print("🔄 Typed Event Payloads:")
    print("   price.proposal: {proposal_id, product_id, previous_price, proposed_price}")
    print("   price.update: {proposal_id, product_id, final_price}")
    print("   chat.prompt: {trace_id, user, action, duration_ms}")
    print("   chat.tool_call: {trace_id, tool_name, action, duration_ms}")
    
    print("\n🌉 Activity Bridge:")
    print("   • Subscribes to all bus events")
    print("   • Supports both typed and legacy payloads")
    print("   • Maps events to Activity feed display")
    print("   • Provides real-time agent interaction visibility")

def demo_value_proposition():
    """Show the value for IRWA."""
    print("\n💎 VALUE PROPOSITION FOR IRWA")
    print("=" * 50)
    
    print("🎯 Intelligent Agent Specialization:")
    print("   • UIA: Natural language processing & task routing")
    print("   • POA: Domain-specific pricing optimization expertise")
    print("   • Clear separation of concerns and responsibilities")
    
    print("\n🔄 True Multi-Agent Communication:")
    print("   • Event-driven architecture with typed payloads")
    print("   • Asynchronous inter-agent messaging")
    print("   • Scalable to additional specialized agents")
    
    print("\n🧠 AI-Powered Decision Making:")
    print("   • LLM-driven algorithm selection based on context")
    print("   • Adaptive pricing strategies per user intent")
    print("   • Explainable AI with decision rationale")
    
    print("\n📊 Real-Time Observability:")
    print("   • Complete agent interaction tracing")
    print("   • Performance monitoring and metrics")
    print("   • Transparent multi-agent workflow visibility")

def check_system_status():
    """Check if core components are available."""
    print("\n🔧 SYSTEM STATUS CHECK")
    print("=" * 50)
    
    # Check databases
    market_db = Path("data/market.db")
    app_db = Path("app/data.db")
    print(f"📊 Market Database: {'✅ Available' if market_db.exists() else '❌ Missing'}")
    print(f"📱 App Database: {'✅ Available' if app_db.exists() else '❌ Missing'}")
    
    # Check data counts
    if market_db.exists():
        try:
            with sqlite3.connect(market_db) as conn:
                count = conn.execute("SELECT COUNT(*) FROM pricing_list").fetchone()[0]
                print(f"📈 Market Products: {count} items")
        except Exception as e:
            print(f"📈 Market Products: Error - {e}")
    
    # Check core imports
    components = [
        ("UserInteractionAgent", "core.agents.user_interact.user_interaction_agent"),
        ("PricingOptimizerAgent", "core.agents.pricing_optimizer"),
        ("Activity Service", "app.ui.services.activity"),
    ]
    
    for name, module in components:
        try:
            __import__(module)
            print(f"🔧 {name}: ✅ Available")
        except Exception as e:
            print(f"🔧 {name}: ⚠️  Import issue - {e}")
    
    # Check API keys
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    
    if has_openrouter or has_openai:
        print(f"🔑 LLM API Key: ✅ Available ({'OpenRouter' if has_openrouter else 'OpenAI'})")
        print("   → Full AI functionality enabled")
    else:
        print("🔑 LLM API Key: ⚠️  Not configured")
        print("   → Fallback mode - deterministic algorithm selection")

def main():
    """Run the complete demo presentation."""
    quick_setup()
    demo_architecture()
    demo_scenarios()
    demo_ai_features()
    demo_event_system()
    demo_value_proposition()
    check_system_status()
    
    print("\n" + "=" * 50)
    print("🎉 FluxPricer AI Demo Setup Complete!")
    print("=" * 50)
    print("📋 Next Steps for Live Demo:")
    print("   1. Run: streamlit run app/streamlit_app.py")
    print("   2. Navigate to Chat tab")
    print("   3. Try: 'What laptops do we have under LKR 100,000?'")
    print("   4. Try: 'Optimize HP Pavilion pricing for maximum profit'")
    print("   5. Check Activity tab for agent interactions")
    print()
    print("💡 Key Demo Points:")
    print("   • Show simple vs complex query handling")
    print("   • Highlight AI algorithm selection reasoning")
    print("   • Demonstrate real-time activity monitoring")
    print("   • Explain multi-agent architecture benefits")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Demo setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo setup failed: {e}")
        import traceback
        traceback.print_exc()