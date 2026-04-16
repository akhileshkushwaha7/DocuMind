import json
import redis.asyncio as aioredis
from app.core.config import settings

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

async def get_cached(key: str):
    r = await get_redis()
    val = await r.get(key)
    return json.loads(val) if val else None

async def set_cached(key: str, value: dict, ttl: int = 60):
    r = await get_redis()
    await r.set(key, json.dumps(value), ex=ttl)

async def invalidate(key: str):
    r = await get_redis()
    await r.delete(key)