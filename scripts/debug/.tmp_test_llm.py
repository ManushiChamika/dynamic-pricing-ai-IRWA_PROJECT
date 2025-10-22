import os
os.environ["DEBUG_LLM"] = "1"

from core.agents.llm_client import get_llm_client

llm = get_llm_client()
print(f"LLM available: {llm.is_available()}")

try:
    response = llm.chat([
        {"role": "system", "content": "You are a helpful assistant that creates concise, meaningful thread titles."},
        {"role": "user", "content": "Generate a 4-6 word title for a conversation about testing a dynamic pricing system."},
    ], max_tokens=50, temperature=0.3)
    print(f"Response: {repr(response)}")
    print(f"Response length: {len(response)}")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
