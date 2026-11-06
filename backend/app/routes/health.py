import asyncio
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.config import settings
from app.db.session import async_session
from app.models import _utcnow

router = APIRouter()
logger = logging.getLogger(__name__)


async def _check_database() -> bool:
    if async_session is None:
        return False

    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.warning("Database health check failed", exc_info=True)
        return False


async def _check_redis() -> bool:
    client = None
    try:
        client = Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        await client.ping()
        return True
    except Exception:
        logger.warning("Redis health check failed", exc_info=True)
        return False
    finally:
        if client is not None:
            try:
                await client.close()
            except Exception:
                logger.debug("Redis health-check client close failed", exc_info=True)


@router.get("/health")
async def health() -> JSONResponse:
    database_ok, redis_ok = await asyncio.gather(
        _check_database(),
        _check_redis(),
    )
    services = {
        "database": "available" if database_ok else "unavailable",
        "redis": "available" if redis_ok else "unavailable",
    }
    healthy = database_ok and redis_ok
    payload = {
        "status": "healthy" if healthy else "degraded",
        "version": settings.APP_VERSION,
        "timestamp": _utcnow().isoformat(),
        "services": services,
    }
    return JSONResponse(status_code=200 if healthy else 503, content=payload)
