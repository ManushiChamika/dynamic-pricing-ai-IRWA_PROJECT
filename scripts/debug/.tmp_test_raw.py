from core.agents.llm_client import get_llm_client

llm = get_llm_client()
provider = llm._providers[0]

print(f"Testing provider: {provider['name']}")
print(f"Model: {provider['model']}")

try:
    resp = provider["client"].chat.completions.create(
        model=provider["model"],
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello"},
        ],
        max_tokens=50,
        temperature=0.3,
    )
    
    print(f"Response object: {resp}")
    print(f"Choices: {resp.choices}")
    if resp.choices:
        print(f"First choice: {resp.choices[0]}")
        print(f"Message: {resp.choices[0].message}")
        print(f"Content: {resp.choices[0].message.content}")
        print(f"Content type: {type(resp.choices[0].message.content)}")
        print(f"Content repr: {repr(resp.choices[0].message.content)}")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
