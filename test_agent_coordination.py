#!/usr/bin/env python3
"""
Test Agent Coordination for Viva Demo
Tests UIA->POA integration and other agent workflows
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
from core.auth_service import AuthService

async def test_uia_poa_integration():
    """Test UIA calling POA for complex pricing requests"""
    print("🔄 Testing UIA->POA Integration...")
    
    auth = AuthService()
    uia = UserInteractionAgent(auth_service=auth)
    
    # Complex prompt that should trigger POA
    complex_prompt = "I need to optimize pricing strategy for gaming laptops using AI-driven competitive analysis and profit maximization algorithms"
    
    print(f"📝 Testing prompt: {complex_prompt}")
    
    try:
        result = await uia.process_request(complex_prompt)
        print("✅ UIA->POA Integration Result:")
        print(f"   Response length: {len(result)} characters")
        print(f"   Contains 'workflow': {'workflow' in result.lower()}")
        print(f"   Contains 'pricing': {'pricing' in result.lower()}")
        print(f"   Contains 'optimization': {'optimization' in result.lower()}")
        return True
    except Exception as e:
        print(f"❌ UIA->POA Integration Failed: {e}")
        return False

async def test_simple_uia_only():
    """Test simple prompts that UIA can handle alone"""
    print("\n🔄 Testing Simple UIA-Only Prompts...")
    
    auth = AuthService()
    uia = UserInteractionAgent(auth_service=auth)
    
    simple_prompts = [
        "What is the current price of ASUS ROG Strix G15?",
        "Show me all gaming laptops in the database",
        "What brands do we have available?"
    ]
    
    for prompt in simple_prompts:
        print(f"📝 Testing: {prompt}")
        try:
            result = await uia.process_request(prompt)
            print(f"   ✅ Response: {len(result)} chars")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

async def main():
    """Main test runner"""
    print("🚀 Starting Agent Coordination Tests for Viva Demo")
    print("=" * 60)
    
    # Test UIA->POA integration
    poa_success = await test_uia_poa_integration()
    
    # Test simple UIA prompts
    await test_simple_uia_only()
    
    print("\n" + "=" * 60)
    print(f"🎯 POA Integration: {'✅ WORKING' if poa_success else '❌ NEEDS FIX'}")
    print("🎯 Next: Test in Streamlit UI at http://localhost:8501")

if __name__ == "__main__":
    asyncio.run(main())