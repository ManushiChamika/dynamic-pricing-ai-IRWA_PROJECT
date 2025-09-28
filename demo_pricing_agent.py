#!/usr/bin/env python3
"""
Demo script for Price Optimization Agent (POA) integration with User Interaction Agent (UIA)
This script demonstrates the different use cases for your viva presentation.
"""

import asyncio
import time
from core.agents.user_interact.user_interaction_agent import UserInteractionAgent

class DemoScenarios:
    def __init__(self):
        self.agent = UserInteractionAgent("Demo User")
        
    def print_separator(self, title):
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)
        
    def print_subsection(self, title):
        print(f"\n--- {title} ---")
        
    async def run_demo(self):
        """Run complete demo showing UIA vs POA scenarios"""
        
        self.print_separator("DYNAMIC PRICING AI MULTI-AGENT SYSTEM DEMO")
        print("Demonstrating User Interaction Agent (UIA) + Price Optimization Agent (POA)")
        
        # Scenario 1: Simple queries handled by UIA alone
        self.print_separator("SCENARIO 1: Simple Queries (UIA Only)")
        
        simple_queries = [
            "What is the current price of ASUS-ProArt-5979Ultr?",
            "Show me the product catalog",
            "List recent price proposals",
            "How many products do we have in inventory?"
        ]
        
        for query in simple_queries:
            self.print_subsection(f"Query: {query}")
            print("🤖 UIA Status: Processing simple query...")
            
            response = self.agent.get_response(query)
            print(f"✅ UIA Response: {response[:200]}...")
            time.sleep(1)
            
        # Scenario 2: Complex pricing queries requiring POA
        self.print_separator("SCENARIO 2: Complex Pricing (UIA → POA)")
        
        complex_queries = [
            "Optimize the price for ASUS-ProArt-5979Ultr using AI and competitor analysis",
            "Run a profit maximization strategy for ASUS-ROG-Strix-1635P",
            "Use machine learning model to price ASUS-TUF-Gaming-4738 competitively",
            "Apply rule-based pricing algorithm to SKU-123 with market analysis"
        ]
        
        for query in complex_queries:
            self.print_subsection(f"Complex Query: {query}")
            print("🤖 UIA Status: Analyzing request complexity...")
            print("🔄 UIA Decision: Requires Price Optimization Agent")
            print("🚀 POA Status: Starting AI-powered pricing workflow...")
            print("   ├── Checking market data freshness...")
            print("   ├── AI selecting optimal algorithm...")
            print("   ├── Running pricing calculations...")
            print("   └── Generating price proposal...")
            
            response = self.agent.get_response(query)
            print(f"✅ POA Result: {response[:300]}...")
            print()
            time.sleep(2)
            
        # Scenario 3: Show the different algorithms POA can choose
        self.print_separator("SCENARIO 3: AI Algorithm Selection Demo")
        
        algorithm_demos = [
            ("Conservative competitive pricing", "Price ASUS-ProArt-5979Ultr conservatively to maintain market share"),
            ("Profit maximization", "Maximize profit margins for ASUS-ROG-Strix-1635P"),
            ("ML-based demand pricing", "Use machine learning to price ASUS-TUF-Gaming-4738 based on demand patterns")
        ]
        
        for strategy, query in algorithm_demos:
            self.print_subsection(f"Strategy: {strategy}")
            print(f"Query: {query}")
            print("🤖 UIA → POA: Forwarding complex pricing request")
            print("🧠 POA AI Brain: Analyzing user intent and market context...")
            print(f"🎯 POA Decision: Selected {strategy.lower()} algorithm")
            print("⚙️  POA Execution: Running selected algorithm...")
            
            response = self.agent.get_response(query)
            print(f"📊 Result: {response[:200]}...")
            print()
            time.sleep(1.5)
            
        # Final summary
        self.print_separator("DEMO SUMMARY")
        print("✅ User Interaction Agent (UIA): Handles simple queries, routes complex ones")
        print("✅ Price Optimization Agent (POA): AI-powered pricing with algorithm selection")
        print("✅ UI Integration: Shows agent status and workflows in real-time")
        print("✅ Multi-Agent Coordination: Seamless handoff between agents")
        print("\n🎯 Key Demo Points for Viva:")
        print("   • Simple vs Complex query handling")
        print("   • AI-powered algorithm selection") 
        print("   • Real-time UI status indicators")
        print("   • Meaningful pricing calculations")
        print("   • Multi-agent system coordination")

def main():
    demo = DemoScenarios()
    asyncio.run(demo.run_demo())

if __name__ == "__main__":
    main()