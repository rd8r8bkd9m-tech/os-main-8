"""Compatibility helpers for Pydantic model serialization/copying.

Provide safe wrappers around `model_dump` / `model_copy` which call the
appropriate method if present, otherwise fall back to older APIs such as
`dict()` / `copy()` or plain Python conversions. The wrappers accept any
object and are annotated to return `Any` so static checkers (pyright) will
not complain about missing attributes on model types.
"""
from __future__ import annotations

from typing import Any


def safe_model_dump(obj: Any, **kwargs: Any) -> Any:
    """Return a serializable representation of ``obj``.

    Tries to call ``obj.model_dump(**kwargs)``. If that method does not
    exist, falls back to ``obj.dict(**kwargs)`` or the object itself.
    """
    # Prefer Pydantic v2 API when available
    method = getattr(obj, "model_dump", None)
    if callable(method):
        return method(**kwargs)

    # Older Pydantic / dataclass fallback
    method = getattr(obj, "dict", None)
    if callable(method):
        try:
            return method(**kwargs)
        except TypeError:
            # Some dict()-like methods don't accept our kwargs
            return method()

    # Last resort: return the object as-is
    return obj


def safe_model_copy(obj: Any, **kwargs: Any) -> Any:
    """Return a copy of ``obj``.

    Tries to call ``obj.model_copy(**kwargs)`` then ``obj.copy(**kwargs)``.
    If neither exists, returns the original object (caller should be
    careful and may choose to copy via ``copy.copy`` or ``copy.deepcopy``).
    """
    method = getattr(obj, "model_copy", None)
    if callable(method):
        return method(**kwargs)

    method = getattr(obj, "copy", None)
    if callable(method):
        try:
            return method(**kwargs)
        except TypeError:
            return method()

    return obj
