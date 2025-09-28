#!/usr/bin/env python3
"""
IRWA Viva Demo - Multi-Agent System Presentation
===============================================

Final presentation script for demonstrating the multi-agent pricing system.
Run this before your viva to ensure everything is ready.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def pre_demo_checklist():
    """Run pre-demo checklist to ensure everything is ready."""
    print("=" * 60)
    print("    IRWA VIVA - MULTI-AGENT SYSTEM DEMO CHECKLIST")
    print("=" * 60)
    
    checks = []
    
    # 1. Database checks
    market_db = Path("data/market.db")
    app_db = Path("app/data.db")
    
    if market_db.exists():
        try:
            with sqlite3.connect(market_db) as conn:
                count = conn.execute("SELECT COUNT(*) FROM pricing_list").fetchone()[0]
                checks.append(f"[OK] Market Database: {count} products available")
        except Exception as e:
            checks.append(f"[WARN] Market Database: Error - {e}")
    else:
        checks.append("[FAIL] Market Database: Missing")
    
    checks.append(f"[{'OK' if app_db.exists() else 'WARN'}] App Database: {'Available' if app_db.exists() else 'Will be created'}")
    
    # 2. Component checks (without importing Streamlit components)
    core_components = [
        ("UserInteractionAgent", "core.agents.user_interact.user_interaction_agent"),
        ("PricingOptimizerAgent", "core.agents.pricing_optimizer"),
    ]
    
    for name, module in core_components:
        try:
            __import__(module)
            checks.append(f"[OK] {name}: Ready")
        except Exception as e:
            checks.append(f"[FAIL] {name}: {e}")
    
    # Check UI components separately
    ui_files = [
        ("Chat Interface", "app/ui/views/chat.py"),
        ("Activity View", "app/ui/views/activity_view.py"),
        ("Dashboard", "app/ui/views/dashboard.py"),
        ("Streamlit App", "app/streamlit_app.py"),
    ]
    
    for name, filepath in ui_files:
        if Path(filepath).exists():
            checks.append(f"[OK] {name}: File available")
        else:
            checks.append(f"[FAIL] {name}: File missing")
    
    # 3. API Key check
    has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    
    if has_openrouter or has_openai:
        checks.append(f"[OK] LLM API: {'OpenRouter' if has_openrouter else 'OpenAI'} configured")
    else:
        checks.append("[WARN] LLM API: No key configured (fallback mode)")
    
    # 4. Environment setup
    env_vars = {
        "DEBUG_LLM": "1",
        "SOUND_NOTIFICATIONS": "0",
        "UI_REQUIRE_LOGIN": "0",
        "STRICT_AI_SELECTION": "false"
    }
    
    for key, value in env_vars.items():
        os.environ.setdefault(key, value)
    
    checks.append("[OK] Environment: Demo configuration applied")
    
    # Print all checks
    for check in checks:
        print(check)
    
    # Overall status
    failed_checks = [c for c in checks if c.startswith("[FAIL]")]
    if failed_checks:
        print(f"\n[ATTENTION] {len(failed_checks)} critical issues found!")
        return False
    else:
        print(f"\n[SUCCESS] All {len(checks)} checks passed - Ready for demo!")
        return True

def demo_script():
    """Print the demo script for the presentation."""
    print("\n" + "=" * 60)
    print("                  DEMO SCRIPT")
    print("=" * 60)
    
    print("""
[STEP 1] Start the Application
   Command: streamlit run app/streamlit_app.py
   URL: http://localhost:8501
   
[STEP 2] Show System Architecture (Chat Tab)
   - Explain the multi-agent design
   - Point out UIA vs POA specialization
   - Highlight event-driven communication

[STEP 3] Demonstrate Simple Query (UIA Direct Handling)
   Query: "What laptops do we have under LKR 100,000?"
   Expected: UIA uses list_inventory tool directly
   Point out: No agent delegation needed for simple queries

[STEP 4] Switch to Activity Tab
   - Show empty activity feed initially
   - Explain real-time agent monitoring
   - Return to Chat tab

[STEP 5] Demonstrate Complex Query (UIA -> POA Delegation)
   Query: "Optimize HP Pavilion pricing for maximum profit"
   Expected: 
   - UIA recognizes complex pricing task
   - UIA calls run_pricing_workflow tool
   - POA performs AI algorithm selection
   - POA analyzes market context
   - Response shows algorithm choice + rationale

[STEP 6] Check Activity Tab
   Expected to show:
   - chat.prompt event (user query)
   - chat.tool_call event (run_pricing_workflow)
   - price.proposal event (POA result)
   - Real-time inter-agent communication

[STEP 7] Explain AI Decision Making
   - Show how POA selected algorithm based on "maximum profit"
   - Explain market context analysis
   - Highlight explainable AI reasoning

[STEP 8] Demo Value Points
   - True multi-agent architecture
   - Intelligent task delegation
   - AI-powered decision making
   - Real-time observability
   - Scalable event-driven design
""")

def key_talking_points():
    """Print key talking points for the viva."""
    print("\n" + "=" * 60)
    print("               KEY TALKING POINTS")
    print("=" * 60)
    
    print("""
[ARCHITECTURE] Multi-Agent Design
   - UserInteractionAgent: Natural language processing & routing
   - PricingOptimizerAgent: Domain-specific optimization expertise  
   - Clear separation of concerns and responsibilities
   - Event-driven communication with typed payloads

[AI INTEGRATION] Intelligent Decision Making
   - LLM-driven algorithm selection based on user intent
   - Context-aware pricing strategies (profit vs competitive)
   - Explainable AI with decision rationale
   - Adaptive behavior based on market conditions

[SCALABILITY] Event-Driven Architecture
   - Asynchronous inter-agent messaging
   - Typed event payloads for reliability
   - Activity bridge for UI integration
   - Easy to add new specialized agents

[OBSERVABILITY] Real-Time Monitoring
   - Complete agent interaction tracing
   - Performance metrics and duration tracking
   - Transparent multi-agent workflow visibility
   - Debug and audit capabilities

[IRWA ALIGNMENT] Responsible AI Features
   - Explainable algorithm selection
   - Transparent decision processes
   - Activity logging for accountability
   - User-controllable AI behavior
""")

def troubleshooting():
    """Print troubleshooting guide."""
    print("\n" + "=" * 60)
    print("                TROUBLESHOOTING")
    print("=" * 60)
    
    print("""
[ISSUE] Port 8501 already in use
   Solution: Kill existing Streamlit process or use different port
   Command: streamlit run app/streamlit_app.py --server.port 8502

[ISSUE] No data in market database
   Solution: Run data population script
   Command: python scripts/populate_sri_lanka_laptop_store.py

[ISSUE] UIA -> POA delegation not working
   Check: run_pricing_workflow in UserInteractionAgent functions_map
   File: core/agents/user_interact/user_interaction_agent.py:476

[ISSUE] Activity feed empty
   Check: Event bus connectivity and activity bridge
   File: app/ui/services/activity.py

[ISSUE] No LLM responses
   Check: API key configuration in environment
   Fallback: Deterministic algorithm selection still works

[BACKUP DEMO] If live demo fails
   Run: python quick_demo_ascii.py
   Shows: System architecture and capabilities without UI
""")

def main():
    """Run the complete pre-demo preparation."""
    success = pre_demo_checklist()
    demo_script()
    key_talking_points()
    troubleshooting()
    
    print("\n" + "=" * 60)
    if success:
        print("    [READY] Multi-Agent System Demo Prepared!")
        print("    Command: streamlit run app/streamlit_app.py")
    else:
        print("    [ATTENTION] Please resolve issues before demo")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[STOP] Demo preparation interrupted")
    except Exception as e:
        print(f"\n[ERROR] Demo preparation failed: {e}")
        import traceback
        traceback.print_exc()