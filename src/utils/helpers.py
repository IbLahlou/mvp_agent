import json
from typing import Any, Dict
from datetime import datetime

def serialize_datetime(obj: Any) -> str:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def load_json_safe(json_str: str) -> Dict:
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON"}

def format_response(response: str, metadata: Dict = None) -> Dict:
    return {
        "response": response,
        "metadata": metadata or {},
        "timestamp": serialize_datetime(datetime.utcnow())
    }