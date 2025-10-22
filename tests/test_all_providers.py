import os

from core.agents.llm_client import LLMClient

llm = LLMClient()

print(f"\nAvailable providers: {[p['name'] for p in llm._providers]}")

for idx, provider in enumerate(llm._providers):
    print(f"\n=== Testing Provider {idx}: {provider['name']} (model: {provider['model']}) ===")
    llm._set_active_provider(idx)
    
    try:
        result = llm.chat([
            {"role": "user", "content": "Say 'hello world' and nothing else"}
        ], max_tokens=200, temperature=0.3)
        
        print(f"SUCCESS: '{result}'")
        print(f"Completion tokens: {llm.last_usage.get('completion_tokens', 'N/A')}")
        break
        
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {str(e)[:100]}")
        continue

print("\n=== Done ===")

