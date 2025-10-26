import re

def fix_test_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    new_lines = []
    in_test_func = False
    client_added = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith('def test_'):
            in_test_func = True
            client_added = False
            new_lines.append(line)
        elif in_test_func and not client_added and line.strip() and not line.strip().startswith('monkeypatch'):
            indent = len(line) - len(line.lstrip())
            new_lines.append(' ' * indent + 'client = make_test_client()')
            new_lines.append(line)
            client_added = True
            in_test_func = False
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'Fixed {filepath}')

fix_test_file('backend/tests/test_catalog_api.py')
fix_test_file('backend/tests/test_prices_api.py')
