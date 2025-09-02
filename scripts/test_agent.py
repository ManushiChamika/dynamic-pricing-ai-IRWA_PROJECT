# scripts/test_agent.py
from core.agents.user_interact.user_interaction_agent import UserInteractionAgent

if __name__ == "__main__":
    agent = UserInteractionAgent("Tester")
    print(agent.get_response("trending products"))
    print()
    print(agent.get_response("which products are rising"))
