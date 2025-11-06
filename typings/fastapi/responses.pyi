from typing import Any, Optional

class StreamingResponse:
    def __init__(
        self,
        content: Any,
        status_code: int = ...,
        headers: dict[str, str] | None = ...,
        media_type: str | None = ...,
    ) -> None: ...

__all__ = ["StreamingResponse"]
