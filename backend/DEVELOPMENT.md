# VerifAI Backend — Development & Operations Guide

## Quick Start (Local)

```bash
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate          # Windows
source venv/bin/activate         # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env           # Windows
cp .env.example .env             # macOS / Linux
# Fill in ANTHROPIC_API_KEY and TAVILY_API_KEY in .env

# 4. Start the backend (SINGLE WORKER — required)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

---

## ⚠️ Critical: Single-Worker Requirement

The current `JobStore` is an **in-memory dictionary** (`app/services/job_store.py`).

| Mode | Safe? | Reason |
|------|-------|--------|
| `--workers 1` (default) | ✅ Yes | Single process, shared memory |
| `--workers 2+` | ❌ No | Each worker gets its own isolated memory. A job created by Worker A is invisible to Worker B. `GET /research/{job_id}` returns 404. |
| `gunicorn --workers 2+` | ❌ No | Same issue — OS-level fork isolation |
| Kubernetes replicas > 1 | ❌ No | Same issue across pods |

The application **logs a warning at startup** if `WEB_CONCURRENCY > 1` is detected.

**Never run with multiple workers until JobStore is replaced with a shared store (Redis, database, etc.).**

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health check |
| `POST` | `/research` | Submit a research query → returns `job_id` |
| `GET` | `/research/{job_id}` | Poll agent statuses |
| `GET` | `/research/{job_id}/result` | Fetch completed report or error |

### Status codes for `GET /research/{job_id}/result`

| Code | Meaning |
|------|---------|
| `200` | Report ready |
| `202` | Still running — keep polling |
| `404` | Job not found |
| `500` | Pipeline failed — structured `ResearchErrorResponse` returned |

---

## Failure Handling

When an agent fails (API error, validation error, etc.):

1. `execute_workflow()` catches the exception after all retries are exhausted.
2. `state.error` is **guaranteed** to be set (`ErrorDetail` with stage, message, retry_count).
3. The failed agent's `agent_status` entry is set to `"error"`.
4. `GET /research/{job_id}/result` returns **HTTP 500** with the error detail.
5. The frontend reads the 500 and displays the error state — **polling stops immediately**.

---

## Running Tests

```bash
# Compile check
python -m compileall app

# Mock end-to-end test (no real API keys needed)
python tests/test_e2e.py
```

---

## Production Notes

- Replace `JobStore` with a Redis or database-backed store before scaling beyond one process.
- Set `CORS_ALLOWED_ORIGINS` to your frontend's production domain.
- Set `DEBUG=false` (default).
- Do **not** mount the `.env` file into production containers — use secrets management instead.
