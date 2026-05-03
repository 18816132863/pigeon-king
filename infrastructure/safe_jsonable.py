"""safe_jsonable — canonical recursive JSON sanitizer for V92+ architecture.

Converts dataclasses, enums, Path objects, Pydantic models, and arbitrary
objects into JSON-safe primitives while preserving field structure.

Placed in infrastructure/ as a shared utility — imported by all gate scripts,
orchestrators, and report generators that write JSON.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any


def safe_jsonable(obj: Any) -> Any:
    """Recursively convert any Python object to a JSON-safe representation.

    Order of resolution:
      1. Primitives (str, int, float, bool, None) → pass through
      2. Enum → .value
      3. Path → str(path)
      4. Dataclass → safe_jsonable(asdict(obj))
      5. dict → {str(k): safe_jsonable(v)}
      6. list/tuple/set → [safe_jsonable(x)]
      7. Pydantic → safe_jsonable(obj.model_dump())
      8. .dict() method → safe_jsonable(obj.dict())
      9. __dict__ → safe_jsonable(vars(obj))
     10. Fallback → str(obj)

    This preserves dataclass field structure (no lossy str() on whole objects).
    """
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Path):
        return str(obj)
    if is_dataclass(obj) and not isinstance(obj, type):
        return safe_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): safe_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [safe_jsonable(x) for x in obj]
    if hasattr(obj, "model_dump"):
        return safe_jsonable(obj.model_dump())
    if hasattr(obj, "dict"):
        try:
            return safe_jsonable(obj.dict())
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return safe_jsonable(vars(obj))
    return str(obj)
