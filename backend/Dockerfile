# VerifAI Backend — Production Dockerfile
# Base: Python 3.12 slim for minimal attack surface
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
# curl is required by the HEALTHCHECK instruction below
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer-caching benefit)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application source code
COPY app/ ./app/

# Expose the API port
EXPOSE 8000

# ── Health check ────────────────────────────────────────────────────────────
# Docker will poll /health every 30 s.
# The container is considered healthy after 1 successful response and
# unhealthy after 3 consecutive failures.
# start-period gives the app time to initialise before counting failures.
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Start command ────────────────────────────────────────────────────────────
# IMPORTANT: --workers 1 is required.
# The in-memory JobStore is not shared across OS processes.
# Running multiple workers causes "Job not found" errors on the polling endpoint.
# Uvicorn handles SIGTERM gracefully by default (drains in-flight requests).
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1"]
