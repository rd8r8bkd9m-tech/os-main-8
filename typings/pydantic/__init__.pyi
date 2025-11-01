from typing import Any, Callable, Dict, Optional, TypeVar

_T = TypeVar("_T")

class BaseModel:
    def __init__(self, **data: Any) -> None: ...
    def dict(self, *args: Any, **kwargs: Any) -> Dict[str, Any]: ...
    def model_dump(self, *args: Any, **kwargs: Any) -> Any: ...
    def model_copy(self, *args: Any, **kwargs: Any) -> Any: ...


def Field(
    default: Any = ...,
    *,
    default_factory: Optional[Callable[[], Any]] = ...,
    alias: Optional[str] = ...,
    description: Optional[str] = ...,
    ge: Optional[float] = ...,
    le: Optional[float] = ...,
    min_length: Optional[int] = ...,
    max_length: Optional[int] = ...,
    # Allow extra keyword args such as `pattern` used in the codebase
    **kwargs: Any,
) -> Any: ...


def field_validator(*fields: str, **kwargs: Any) -> Callable[[Callable[..., _T]], Callable[..., _T]]: ...

class ValidationError(Exception):
    def errors(self) -> list[dict[str, Any]]: ...

__all__ = ["BaseModel", "Field", "ValidationError", "field_validator"]
