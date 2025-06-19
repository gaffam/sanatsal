from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from redis import asyncio as aioredis
from cachetools import TTLCache

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting per client IP."""

    def __init__(self, app, max_requests: int = 100, window: int = 60, redis_url: str | None = None):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window
        self.redis = None
        self.clients: TTLCache | None = None
        if redis_url:
            self.redis = aioredis.from_url(
                redis_url, encoding="utf-8", decode_responses=True
            )
        else:
            # local fallback with limited memory
            self.clients = TTLCache(maxsize=10000, ttl=window)

    async def dispatch(self, request: Request, call_next):
        client = request.client.host
        if self.redis:
            key = f"rl:{client}"
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, self.window)
            if count > self.max_requests:
                return Response(status_code=429)
        else:
            count = self.clients.get(client, 0)
            if count >= self.max_requests:
                return Response(status_code=429)
            self.clients[client] = count + 1
        response = await call_next(request)
        return response
