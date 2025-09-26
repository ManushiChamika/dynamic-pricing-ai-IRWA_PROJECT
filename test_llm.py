#!/usr/bin/env python3
import os
import sys
sys.path.append('.')

# Load .env manually
if os.path.exists('.env'):
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and not os.getenv(key):
                    os.environ[key] = value

print('Environment variables:')
print('OPENROUTER_API_KEY set:', bool(os.getenv('OPENROUTER_API_KEY')))
print('OPENROUTER_MODEL:', os.getenv('OPENROUTER_MODEL'))
print('OPENROUTER_BASE_URL:', os.getenv('OPENROUTER_BASE_URL'))

try:
    from app.llm_client import get_llm_client
    llm = get_llm_client()
    print('Provider:', llm.provider())
    print('Model:', llm.model)
    print('Available:', llm.is_available())

    if llm.is_available():
        print('Testing chat...')
        response = llm.chat([{'role': 'user', 'content': 'What model are you? Respond with just the model name.'}], max_tokens=20)
        print('Response:', repr(response))
except Exception as e:
    print('Error:', e)
    import traceback
    traceback.print_exc()