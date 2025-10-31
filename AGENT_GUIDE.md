Agent Guide

Quick commands

- Export OpenAPI: `python scripts/export_openapi.py`
- Generate tool manifest: `python scripts/generate_tool_manifest.py`

Purpose

- `openapi.json` enables client generation and frontend type exports.
- `agent_tools.json` provides a machine-friendly view of registered tools.

Notes

- Scripts attempt to import runtime objects; if imports fail they fall back to light source parsing.
- If `python scripts/export_openapi.py` errors with import errors, ensure dependencies are installed and run the full app with `run_full_app.bat` before re-running.

Restart guidance

- Adding these files does not require a server restart. Regenerating `openapi.json` will require re-running the export script; the running server will not automatically pick up `openapi.json` unless you wire it into the app.

Testing credentials

- demo@example.com / 1234567890
