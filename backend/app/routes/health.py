from fastapi import APIRouter
from app.models import _utcnow

router = APIRouter()


from app.config import settings

@router.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": _utcnow().isoformat(),
        "services": {
            "workflow": "available",
            "job_store": "available"
        }
    }
