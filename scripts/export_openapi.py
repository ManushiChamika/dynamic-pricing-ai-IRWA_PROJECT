from pathlib import Path
import json


def main():
    try:
        import os
        os.environ.setdefault("EXPORT_OPENAPI_ONLY", "1")
        from backend.main import app
    except Exception as e:
        print("Failed to import backend.main:app - ensure repository dependencies are installed and the PYTHONPATH includes the repo root")
        raise

    out = Path(__file__).resolve().parent.parent / "openapi.json"
    openapi = app.openapi()
    out.write_text(json.dumps(openapi, indent=2), encoding="utf-8")
    print(f"Wrote OpenAPI spec to {out}")


if __name__ == "__main__":
    main()
