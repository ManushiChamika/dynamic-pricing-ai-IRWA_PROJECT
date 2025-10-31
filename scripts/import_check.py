import importlib
import traceback
import sys

mods = ['core.workflow_templates', 'core.agents.supervisor', 'core.tool_registry']
print('Import check start')
ok = True
for m in mods:
    try:
        importlib.import_module(m)
        print('OK:', m)
    except Exception:
        print('ERR:', m)
        traceback.print_exc()
        ok = False
print('Import check end')
if not ok:
    sys.exit(2)
