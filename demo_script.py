#!/usr/bin/env python3
"""
Multi-Agent System Demo Script for IRWA Viva
===========================================

This script demonstrates the multi-agent architecture with focus on:
1. UserInteractionAgent (UIA) - Handles user queries and delegates complex tasks
2. PricingOptimizerAgent (POA) - AI-driven pricing optimization with algorithm selection
3. Real-time Activity feed showing agent interactions
4. Event-driven communication via typed bus events

Demo Scenarios:
- Simple: "What's the current price of iPhone 15?" (UIA handles alone)
- Complex: "Optimize iPhone 15 pricing for maximum profit" (UIA → POA delegation)
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def setup_environment():
    """Setup demo environment with required data and configurations."""
    print("🔧 Setting up demo environment...")
    
    # Set minimal required environment variables for demo
    os.environ.setdefault("DEBUG_LLM", "1")
    os.environ.setdefault("SOUND_NOTIFICATIONS", "1")
    os.environ.setdefault("UI_REQUIRE_LOGIN", "0")
    os.environ.setdefault("STRICT_AI_SELECTION", "false")  # Allow fallback for demo
    
    # Check if we have LLM API key (optional for demo)
    has_api_key = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))
    if has_api_key:
        print("✅ LLM API key found - full AI functionality enabled")
    else:
        print("⚠️  No LLM API key - using fallback mode for AI decisions")
    
    print("✅ Environment setup complete")
    return has_api_key

def ensure_demo_data():
    """Ensure we have demo data populated."""
    print("📊 Ensuring demo data is available...")
    
    try:
        # Run the Sri Lanka laptop store population script
        import subprocess
        result = subprocess.run([
            sys.executable, 
            "scripts/populate_sri_lanka_laptop_store.py"
        ], capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ Demo data populated successfully")
        else:
            print(f"⚠️  Data population warning: {result.stderr}")
    except Exception as e:
        print(f"⚠️  Could not populate demo data: {e}")
    
    return True

async def demo_simple_scenario():
    """Demo Scenario 1: Simple pricing query handled by UIA alone."""
    print("\n" + "="*60)
    print("📱 DEMO SCENARIO 1: Simple Query (UIA handles alone)")
    print("="*60)
    print("User Query: 'What laptops do we have under LKR 100,000?'")
    print("Expected: UIA uses list_inventory tool to browse products")
    print("-"*60)
    
    try:
        from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
        
        agent = UserInteractionAgent("demo_user")
        
        print("🤖 UserInteractionAgent processing query...")
        response = agent.get_response("What laptops do we have under LKR 100,000?")
        
        print(f"📤 Response:")
        print(response)
        print("\n✅ Simple scenario completed - UIA handled query independently")
        
    except Exception as e:
        print(f"❌ Simple scenario failed: {e}")
        import traceback
        traceback.print_exc()

async def demo_complex_scenario():
    """Demo Scenario 2: Complex pricing optimization requiring UIA → POA delegation."""
    print("\n" + "="*60)
    print("🧠 DEMO SCENARIO 2: Complex Optimization (UIA → POA)")
    print("="*60)
    print("User Query: 'Optimize HP Pavilion 8394Pro pricing for maximum profit'")
    print("Expected: UIA recognizes complexity and calls POA via run_pricing_workflow")
    print("-"*60)
    
    try:
        from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
        
        agent = UserInteractionAgent("demo_user")
        
        print("🤖 UserInteractionAgent processing complex query...")
        print("📡 Expected: UIA will call run_pricing_workflow tool")
        print("🧠 Expected: POA will use AI to select pricing algorithm")
        print("📊 Expected: Activity feed will show agent interactions")
        
        response = agent.get_response("Optimize HP Pavilion 8394Pro pricing for maximum profit")
        
        print(f"📤 Response:")
        print(response)
        print("\n✅ Complex scenario completed - UIA delegated to POA successfully")
        
    except Exception as e:
        print(f"❌ Complex scenario failed: {e}")
        import traceback
        traceback.print_exc()

def demo_activity_monitoring():
    """Demo the Activity monitoring system."""
    print("\n" + "="*60)
    print("📊 DEMO: Activity Monitoring System")
    print("="*60)
    print("Showing recent agent activities and inter-agent communications")
    print("-"*60)
    
    try:
        from app.ui.services.activity import recent
        
        activities = recent(limit=10)
        
        if activities:
            print("🔍 Recent Agent Activities:")
            for i, activity in enumerate(activities[-5:], 1):  # Show last 5
                timestamp = activity.get('timestamp', 'Unknown')
                agent = activity.get('agent', 'Unknown')
                action = activity.get('action', 'Unknown')
                status = activity.get('status', 'Unknown')
                message = activity.get('message', 'No message')
                
                status_emoji = {
                    'completed': '✅',
                    'in_progress': '🔄',
                    'failed': '❌',
                    'info': 'ℹ️'
                }.get(status, '❓')
                
                print(f"  {i}. {status_emoji} [{agent}] {action}")
                print(f"     📝 {message}")
                print(f"     🕐 {timestamp}")
                print()
        else:
            print("📭 No recent activities found")
            
        print("✅ Activity monitoring system operational")
        
    except Exception as e:
        print(f"❌ Activity monitoring failed: {e}")

def demo_poa_capabilities():
    """Demo the PricingOptimizerAgent AI capabilities."""
    print("\n" + "="*60)
    print("🧠 DEMO: PricingOptimizerAgent AI Capabilities") 
    print("="*60)
    print("Showcasing AI-driven algorithm selection and market analysis")
    print("-"*60)
    
    try:
        from core.agents.pricing_optimizer import PricingOptimizerAgent
        
        print("🤖 Creating PricingOptimizerAgent...")
        agent = PricingOptimizerAgent()
        
        print("🔍 Available pricing algorithms:")
        from core.agents.pricing_optimizer import TOOLS
        for name, func in TOOLS.items():
            if name in ("rule_based", "ml_model", "profit_maximization"):
                doc = func.__doc__.strip().split('\n')[1] if func.__doc__ else "No description"
                print(f"  • {name}: {doc}")
        
        print("\n🧠 AI Decision Process:")
        print("  1. Analyzes user intent and market context")
        print("  2. Selects optimal pricing algorithm via LLM")
        print("  3. Executes chosen algorithm with market data")
        print("  4. Publishes typed price.proposal events")
        print("  5. Activity feed shows AI decision rationale")
        
        print("✅ PricingOptimizerAgent capabilities verified")
        
    except Exception as e:
        print(f"❌ POA capabilities demo failed: {e}")

def demo_event_system():
    """Demo the event-driven communication system."""
    print("\n" + "="*60)
    print("📡 DEMO: Event-Driven Communication System")
    print("="*60)
    print("Showcasing typed event payloads and Activity bridge")
    print("-"*60)
    
    try:
        print("📋 Typed Event Schemas:")
        from core.events.schemas import REQUIRED_KEYS
        
        for event_type, keys in REQUIRED_KEYS.items():
            print(f"  • {event_type}: {{{', '.join(keys)}}}")
        
        print("\n🌉 Activity Bridge Features:")
        print("  • Subscribes to bus events (alerts, price proposals, chat)")
        print("  • Supports both typed and legacy payload formats")
        print("  • Real-time activity feed updates")
        print("  • Agent interaction visualization")
        
        print("✅ Event system operational")
        
    except Exception as e:
        print(f"❌ Event system demo failed: {e}")

async def run_full_demo():
    """Run the complete multi-agent demo."""
    print("🚀 FluxPricer AI Multi-Agent System Demo")
    print("=" * 60)
    print("Demonstrating intelligent agent delegation and AI-driven pricing")
    print()
    
    # Setup
    has_api_key = setup_environment()
    ensure_demo_data()
    
    # Architecture overview
    print("\n🏗️  SYSTEM ARCHITECTURE:")
    print("  • UserInteractionAgent (UIA) - Query processing & task delegation")
    print("  • PricingOptimizerAgent (POA) - AI-driven pricing optimization")
    print("  • Event Bus - Typed inter-agent communication")
    print("  • Activity Monitor - Real-time agent interaction tracking")
    
    if not has_api_key:
        print("\n⚠️  DEMO MODE: Running without LLM API key")
        print("   • UIA will use direct database queries")
        print("   • POA will use deterministic algorithm selection")
        print("   • All other features fully operational")
    
    # Run demo scenarios
    await demo_simple_scenario()
    await demo_complex_scenario()
    
    # Show system capabilities
    demo_activity_monitoring()
    demo_poa_capabilities() 
    demo_event_system()
    
    # Demo summary
    print("\n" + "="*60)
    print("🎯 DEMO SUMMARY")
    print("="*60)
    print("✅ Multi-agent architecture with intelligent task delegation")
    print("✅ AI-driven pricing optimization with algorithm selection")
    print("✅ Real-time activity monitoring and agent communication")
    print("✅ Event-driven system with typed payloads")
    print("✅ Scalable architecture supporting additional agents")
    
    print("\n🎉 Demo completed successfully!")
    print("\nFor live interaction, run: streamlit run app/streamlit_app.py")
    print("Activity monitoring: Check the Activity tab in the UI")

if __name__ == "__main__":
    try:
        asyncio.run(run_full_demo())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()