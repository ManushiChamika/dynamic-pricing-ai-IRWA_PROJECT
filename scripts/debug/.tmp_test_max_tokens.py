from core.agents.llm_client import get_llm_client

llm = get_llm_client()
provider = llm._providers[0]

print(f"Testing provider: {provider['name']} with different max_tokens values")
print(f"Model: {provider['model']}")

for max_tok in [50, 100, 200, 500]:
    try:
        resp = provider["client"].chat.completions.create(
            model=provider["model"],
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates concise titles."},
                {"role": "user", "content": "Generate a 4-6 word title for a conversation about testing pricing."},
            ],
            max_tokens=max_tok,
            temperature=0.3,
        )
        
        content = resp.choices[0].message.content if resp.choices else None
        completion_tokens = resp.usage.completion_tokens if resp.usage else 0
        print(f"max_tokens={max_tok:3d} -> content={repr(content)[:80]:80s} tokens={completion_tokens}")
    except Exception as e:
        print(f"max_tokens={max_tok:3d} -> ERROR: {e}")
