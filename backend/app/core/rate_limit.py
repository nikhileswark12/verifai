import hashlib

import redis.asyncio as redis
from redis.exceptions import RedisError
from fastapi import HTTPException, Request

from app.config import settings

RESEARCH_RATE_LIMIT = 10
RESEARCH_RATE_WINDOW_SECONDS = 60


async def enforce_research_rate_limit(request: Request) -> None:
    client_host = request.client.host if request.client else "unknown"
    client_key = hashlib.sha256(client_host.encode("utf-8")).hexdigest()
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        count = await redis_client.eval(
            "local count = redis.call('INCR', KEYS[1]); "
            "if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]); end; "
            "return count",
            1,
            f"verifai:research-rate:{client_key}",
            RESEARCH_RATE_WINDOW_SECONDS,
        )
    except RedisError as exc:
        raise HTTPException(
            status_code=503,
            detail="Research submission is temporarily unavailable.",
        ) from exc
    finally:
        await redis_client.close()

    if int(count) > RESEARCH_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Research submission limit exceeded. Try again in one minute.",
            headers={"Retry-After": str(RESEARCH_RATE_WINDOW_SECONDS)},
        )
