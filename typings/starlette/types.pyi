from typing import Any, Awaitable, Callable, Protocol

class Scope(Protocol):
    def __getitem__(self, key: str) -> Any: ...
    def __setitem__(self, key: str, value: Any) -> None: ...

Receive = Callable[[], Awaitable[Any]]
Send = Callable[[Any], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

__all__ = ["Scope", "Receive", "Send", "ASGIApp"]
