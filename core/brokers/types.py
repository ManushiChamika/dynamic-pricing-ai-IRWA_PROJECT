# core/brokers/types.py
import json
from datetime import datetime, timezone
from typing import Any

def to_jsonable(obj: Any) -> Any:
    """Make any pydantic/dataclass/obj JSON-serializable with ISO datetimes."""
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump()
    elif hasattr(obj, "dict"):
        obj = obj.dict()
    elif hasattr(obj, "__dict__"):
        obj = obj.__dict__
    def _conv(o):
        if isinstance(o, datetime):
            return o.astimezone(timezone.utc).isoformat()
        raise TypeError(f"Not JSON serializable: {type(o)}")
    return json.loads(json.dumps(obj, default=_conv))
