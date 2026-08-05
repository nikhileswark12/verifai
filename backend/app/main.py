from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging import configure_logging
from app.middleware.request_id import RequestIDMiddleware
from app.routes import health, research

configure_logging()
_startup_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown lifecycle hook.

    IMPORTANT — JobStore is in-memory. Running multiple OS processes (e.g.
    uvicorn --workers 2 or gunicorn) will create isolated memory spaces: jobs
    created in worker A will not be visible to worker B.

    Always start with a SINGLE worker:
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
    """
    workers = int(os.getenv("WEB_CONCURRENCY", "1"))
    if workers > 1:
        _startup_logger.warning(
            "JobStore MULTI-WORKER WARNING: WEB_CONCURRENCY=%d. "
            "The in-memory JobStore is NOT shared across OS processes. "
            "Jobs will appear missing when handled by different workers. "
            "Set --workers 1 for local development.",
            workers,
        )
    else:
        _startup_logger.info(
            "JobStore running in single-process mode (PID %d). Job visibility is guaranteed.",
            os.getpid(),
        )
    yield  # application runs here

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root() -> dict:
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


app.include_router(health.router)
app.include_router(research.router)
