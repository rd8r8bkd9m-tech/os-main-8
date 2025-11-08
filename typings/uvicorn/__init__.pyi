from typing import Any

def run(
    app: Any,
    *,
    host: str = ...,
    port: int = ...,
    log_level: str = ...,
    **kwargs: Any
) -> None: ...

__all__ = ["run"]
