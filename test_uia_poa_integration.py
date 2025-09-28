#!/usr/bin/env python3
"""
Test UIA->POA integration and activity logging
"""
import os
from pathlib import Path

# Set environment for testing
os.environ['OPENROUTER_API_KEY'] = 'test'
os.environ['OPENROUTER_BASE_URL'] = 'https://openrouter.ai/api/v1'

# Test UIA->POA integration
def test_uia_poa_integration():
    from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
    
    agent = UserInteractionAgent("test_user")
    
    # Test complex prompt that should trigger POA
    complex_prompts = [
        "Optimize pricing strategy for LAP001 using AI-driven analysis",
        "Maximize profit for laptop LAP002 using advanced algorithms", 
        "Run competitive pricing analysis for LAP003",
        "Use machine learning to optimize price for LAP004"
    ]
    
    # Test simple prompt that should stay with UIA
    simple_prompts = [
        "What's the current price of LAP001?",
        "List all laptops in inventory",
        "Show me market prices"
    ]
    
    print("=== Testing Complex Prompts (should trigger POA) ===")
    for prompt in complex_prompts:
        print(f"\nTesting: {prompt}")
        try:
            response = agent.get_response(prompt)
            print(f"Response: {response[:200]}...")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n=== Testing Simple Prompts (should stay with UIA) ===")
    for prompt in simple_prompts:
        print(f"\nTesting: {prompt}")
        try:
            response = agent.get_response(prompt)
            print(f"Response: {response[:200]}...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_uia_poa_integration()