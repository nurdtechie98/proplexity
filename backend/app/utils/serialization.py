from typing import Any
from pydantic import BaseModel


def serialize_model(obj: Any) -> Any:
    """
    Serialize an object to a JSON-compatible format.
    Handles Pydantic models and nested objects.
    """
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: serialize_model(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_model(item) for item in obj]
    elif hasattr(obj, "__dict__"):
        return {
            k: serialize_model(v)
            for k, v in obj.__dict__.items()
            if not k.startswith("_")
        }
    return obj
