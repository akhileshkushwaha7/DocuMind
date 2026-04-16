import redis.asyncio as aioredis
from fastapi import HTTPException
from app.core.config import settings

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

async def check_rate_limit(user_id: str, max_requests: int = 20, window_seconds: int = 60):
    """Sliding window rate limiter — raises 429 if user exceeds limit."""
    r = await get_redis()
    key = f"rate_limit:chat:{user_id}"

    count = await r.incr(key)
    if count == 1:
        await r.expire(key, window_seconds)

    if count > max_requests:
        ttl = await r.ttl(key)
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Try again in {ttl} seconds."
        )