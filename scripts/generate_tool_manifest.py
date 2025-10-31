from pathlib import Path
import json
import re

OUT = Path(__file__).resolve().parent.parent / "agent_tools.json"
TOOL_REGISTRY_PY = Path(__file__).resolve().parent.parent / "core" / "tool_registry.py"


def from_runtime() -> list:
    try:
        from core.tool_registry import get_tool_registry

        reg = get_tool_registry()
        tools = reg.list_tools()
        return tools
    except Exception as e:
        print(f"Runtime import failed: {e}")
        raise


def from_source_parse() -> list:
    txt = TOOL_REGISTRY_PY.read_text(encoding="utf-8")
    pattern = r"register\(\s*\"(?P<name>[\w_\-]+)\"\s*,\s*\"(?P<desc>[^\"]+)\""
    matches = re.finditer(pattern, txt)
    tools = []
    for m in matches:
        name = m.group("name")
        desc = m.group("desc").strip()
        tools.append({"name": name, "description": desc, "schema": {"type":"object"}})
    return tools


def main():
    try:
        tools = from_runtime()
    except Exception:
        tools = from_source_parse()

    OUT.write_text(json.dumps({"tools": tools}, indent=2), encoding="utf-8")
    print(f"Wrote tool manifest to {OUT}")


if __name__ == "__main__":
    main()
