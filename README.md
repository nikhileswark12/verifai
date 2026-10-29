# VerifAI

VerifAI is an evidence-first, multi-agent research and fact-verification application. It decomposes a question into claims, retrieves web evidence, verifies claims against that evidence, checks for contradictions, and produces a structured report.

## Architecture

- Frontend: React, TypeScript, Vite, Tailwind CSS
- API: FastAPI and Pydantic
- Workflow: LangGraph (Planner → Research → Verification → Contradiction → Report)
- LLM: OpenRouter
- Search: Tavily
- Persistence: PostgreSQL with SQLAlchemy and Alembic
- Background jobs: Celery with Redis

## Local setup

Requirements: Python 3.11+, Node.js/npm, PostgreSQL, and Redis.

### Backend

```bash
git clone https://github.com/nikhileswark12/verifai.git
cd verifai/backend
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set real `OPENROUTER_API_KEY` and `TAVILY_API_KEY` values and configure `DATABASE_URL` for a local PostgreSQL database. Never use a production database for tests. Start PostgreSQL and Redis, then run migrations from `backend/`:

```bash
alembic upgrade head
```

Start each process in a separate terminal from `backend/`:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
celery -A app.worker.celery_app worker --loglevel=info
celery -A app.worker.celery_app beat --loglevel=info
```

The API, Celery worker, and Celery beat are separate processes. Beat is required for scheduled stale-job recovery. PostgreSQL stores job state; Redis is the Celery broker.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

The frontend defaults to `http://localhost:8000` for the API. Override it with `VITE_API_URL` in `frontend/.env.local` if needed. Interactive API documentation is available at `/docs`.

## API

- `GET /health` — API health response
- `POST /research` — submit a query; returns HTTP 202 and a job ID
- `GET /research/{job_id}` — overall status and per-agent status
- `GET /research/{job_id}/result` — report when complete, HTTP 202 while running, or a structured error

## Tests and checks

From `backend/`:

```bash
pip install -r requirements-dev.txt
python -m compileall app
pytest -q tests/test_regression.py
```

Database integration tests require a dedicated disposable PostgreSQL test database. Never point tests that recreate their schema at a development or production database.

From `frontend/`:

```bash
npm ci
npm run lint
npm run build
```

## Model training and data policy

Model training is deliberately outside the application runtime and remains a local, manually controlled workflow. VerifAI does not automatically train or fine-tune models when the API or worker starts. Do not generate or use synthetic data for training. If local training is introduced, use only real, lawfully obtained, documented datasets, validate provenance and quality, and keep datasets, checkpoints, and credentials out of Git.

## Security and deployment

- Keep secrets in environment variables; never commit `.env` files or API keys.
- Set `CORS_ALLOWED_ORIGINS` to exact frontend origins.
- Use a dedicated disposable database for automated tests.
- Configure PostgreSQL backups, Redis availability, and worker/beat process supervision before production use.
- CI checks do not replace a live integration test against configured PostgreSQL, Redis, OpenRouter, and Tavily services.
