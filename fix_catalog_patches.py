import re

file_path = r"C:\Users\SASINDU\Desktop\IRWA Group Repo\dynamic-pricing-ai-IRWA_PROJECT\backend\tests\test_catalog_api.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    'with patch("core.agents.data_collector.repo.DataRepo")',
    'with patch("backend.routers.catalog.DataRepo")'
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed test_catalog_api.py patches")
