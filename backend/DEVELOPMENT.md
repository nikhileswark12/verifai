# VerifAI Backend — Development and Operations

## Prerequisites

Use Python 3.11+, PostgreSQL, Redis, and OpenRouter/Tavily credentials for live research. The backend is database-backed and uses Celery; it is not an in-memory-only application.

## Local startup

From `backend/`:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `OPENROUTER_API_KEY`, `TAVILY_API_KEY`, and a local PostgreSQL `DATABASE_URL` in `.env`. Start PostgreSQL and Redis, then run:

```bash
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
celery -A app.worker.celery_app worker --loglevel=info
celery -A app.worker.celery_app beat --loglevel=info
```

Run the three application processes in separate terminals. Celery beat is needed for the scheduled stale-job sweeper. Keep one API worker unless deployment and connection-pool configuration have been load-tested.

## API contract

| Method | Path | Result |
|---|---|---|
| GET | `/health` | Health and version |
| POST | `/research` | HTTP 202 with `job_id` and `status: accepted` |
| GET | `/research/{job_id}` | Overall `status`, `agent_status`, optional error message |
| GET | `/research/{job_id}/result` | Report on completion, HTTP 202 while running, structured 404/500 error otherwise |

Overall status is `pending`, `running`, `completed`, or `failed`. Agent status values are `pending`, `running`, `done`, or `error`.

## Recovery and failure handling

Jobs and workflow state are stored in PostgreSQL. Celery dispatches execution via Redis. The scheduled sweeper requeues jobs whose heartbeat is older than `JOB_STALE_TIMEOUT`. If Redis is unavailable during submission, the API records a terminal error where possible and returns HTTP 503 instead of silently leaving a pending job.

For production, run API, worker, and beat under a process supervisor. Configure alerting for failed jobs, database failures, and workers that stop heartbeating. Recovered workflows may repeat external searches; agent operations should remain safe to retry.

## Tests

Install test dependencies with `pip install -r requirements-dev.txt`, then run:

```bash
python -m compileall app
pytest -q tests/test_regression.py
```

Database integration tests require a dedicated disposable database. Never point schema-resetting fixtures at production or any database with data that must be preserved.

## Model training and data

Model training is not part of API startup, worker execution, or CI. Keep any training process local and explicitly invoked. Do not use synthetic data. If training is added, use only real, appropriately licensed and documented data, verify provenance, and keep datasets and checkpoints outside version control.
