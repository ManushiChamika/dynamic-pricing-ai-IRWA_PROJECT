from core.agents.llm_client import get_llm_client

llm = get_llm_client()

print(f"Testing all {len(llm._providers)} providers:\n")

for idx, provider in enumerate(llm._providers):
    print(f"Provider {idx}: {provider['name']} ({provider['model']})")
    try:
        resp = provider["client"].chat.completions.create(
            model=provider["model"],
            messages=[
                {"role": "user", "content": "Say hello in 2 words"},
            ],
            max_tokens=20,
            temperature=0.3,
        )
        
        content = resp.choices[0].message.content if resp.choices else None
        print(f"  Response: {repr(content)}")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {str(e)[:100]}")
    print()
