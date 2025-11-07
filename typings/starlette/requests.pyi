from typing import Any

class Request:
    url: Any
    method: str
    headers: Any
    query_params: Any
    path_params: Any
    cookies: Any
    client: Any
    state: Any
    scope: Any
    async def body(self) -> bytes: ...
    async def json(self) -> Any: ...
    async def form(self) -> Any: ...

__all__ = ["Request"]
