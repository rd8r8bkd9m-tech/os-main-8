from typing import Any, Protocol

class ASGIApplication(Protocol):
    async def __call__(self, scope: Any, receive: Any, send: Any) -> None: ...

__all__ = ["ASGIApplication"]
