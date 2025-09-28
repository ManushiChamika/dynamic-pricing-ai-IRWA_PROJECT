#!/usr/bin/env python3

import os
import sys
import warnings
warnings.filterwarnings("ignore")

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def main():
    print("DEBUG: Starting LLM debug test...")
    
    try:
        # Import and create UserInteractionAgent
        from core.agents.user_interact.user_interaction_agent import UserInteractionAgent
        
        print("DEBUG: Creating UserInteractionAgent...")
        agent = UserInteractionAgent(user_name="debug_user")
        
        print("DEBUG: Testing simple response...")
        response = agent.get_response("Hello, can you help me with pricing?")
        
        print(f"DEBUG: Got response: {response}")
        
    except Exception as e:
        print(f"DEBUG: Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()