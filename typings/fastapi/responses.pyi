from typing import Any, Dict, Optional

class StreamingResponse:
    def __init__(
        self,
        content: Any,
        status_code: int = ...,
        headers: Optional[Dict[str, str]] = ...,
        media_type: Optional[str] = ...,
    ) -> None: ...

__all__ = ["StreamingResponse"]
