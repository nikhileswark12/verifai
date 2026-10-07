import os
from celery import Celery
from app.config import settings

celery_app = Celery(
    "verifai_worker",
    broker=settings.CELERY_BROKER_URL,
    include=["app.worker.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # We do not need to store results in Celery backend because Postgres holds all state
    task_ignore_result=True,
    # Idempotency safeguards:
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    beat_schedule={
        "sweep-stale-jobs-every-60s": {
            "task": "sweep_stale_jobs",
            "schedule": 60.0,
        },
    }
)
