"""Server cache and HTTP validators of the explore routes (design §9).

Key = route + canonical query + catalog version. Identical concurrent
requests collapse into one computation; a matching `If-None-Match` answers
304 without computing anything."""

import asyncio
import hashlib
import json
from typing import Awaitable, Callable

from api.models.explore import ExploreQuery
from api.services.explore.filters import parse_filter
from cachetools import TTLCache
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

CACHE_CONTROL = "private, max-age=300"


def canonical_key(route: str, query: ExploreQuery | None, version: int) -> str:
    payload = {"route": route, "version": version}
    if query is not None:
        params = query.model_dump(mode="json", by_alias=True, exclude_none=True)
        params["filter"] = parse_filter(query.filter)
        payload["query"] = params
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def etag_of(key: str) -> str:
    return '"' + hashlib.sha1(key.encode()).hexdigest() + '"'


class ExploreCache:
    def __init__(self, maxsize: int = 1024, ttl: int = 600):
        self.results: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.locks: dict[str, asyncio.Lock] = {}

    async def get(self, key: str, compute: Callable[[], Awaitable[BaseModel]]) -> BaseModel:
        if key in self.results:
            return self.results[key]
        lock = self.locks.setdefault(key, asyncio.Lock())
        async with lock:
            if key in self.results:
                return self.results[key]
            result = await compute()
            self.results[key] = result
        self.locks.pop(key, None)
        return result

    def clear(self) -> None:
        self.results.clear()
        self.locks.clear()


cache = ExploreCache()


async def respond(
    request: Request, key: str, compute: Callable[[], Awaitable[BaseModel]]
) -> Response:
    etag = etag_of(key)
    headers = {"ETag": etag, "Cache-Control": CACHE_CONTROL}
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    result = await cache.get(key, compute)
    return JSONResponse(
        result.model_dump(mode="json", by_alias=True, exclude_none=True),
        headers=headers,
    )
