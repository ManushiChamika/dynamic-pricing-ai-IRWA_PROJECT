import sys
import os
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

os.environ["DEBUG_LLM"] = "1"

from core.agents.user_interact.user_interaction_agent import UserInteractionAgent

uia = UserInteractionAgent(user_name="test", mode="user")

message = "Show me all products in my catalog and identify which ones have pricing that might need attention based on profit margins."

print("Starting stream test...")
print("-" * 80)

parts = []
try:
    for delta in uia.stream_response(message):
        if isinstance(delta, str):
            parts.append(delta)
            sys.stdout.buffer.write(delta.encode('utf-8'))
            sys.stdout.flush()
        elif isinstance(delta, dict):
            print(f"\n[EVENT: {delta}]", flush=True)
except Exception as e:
    print(f"\n\nERROR DURING STREAMING: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()

print("\n" + "-" * 80)
print(f"Total text parts: {len(parts)}")
print(f"Full response:\n{''.join(parts)}")
