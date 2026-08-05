"""
VerifAI — Application Configuration
=====================================
Loads environment variables (from .env locally, or the host environment in
production) and exposes them as a typed Settings singleton.

IMPORTANT: Do NOT add default values for secrets (ANTHROPIC_API_KEY,
TAVILY_API_KEY). Missing secrets raise a clear error at startup rather than
failing silently mid-request.
"""

import os
from dotenv import load_dotenv

# Load .env when present (local development). In production the container's
# environment is pre-populated; load_dotenv() is a no-op if no file exists.
load_dotenv()


def _require(name: str) -> str:
    """Return env var value or raise a descriptive error if missing."""
    value = os.getenv(name, "")
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{name}' is not set. "
            "Set it in your .env file (local) or container environment (production)."
        )
    return value


class Settings:
    APP_NAME: str = "VerifAI API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ── Secrets (validated at startup) ──────────────────────────────────────
    OPENROUTER_API_KEY: str = _require("OPENROUTER_API_KEY")
    TAVILY_API_KEY: str = _require("TAVILY_API_KEY")

    # ── LLM Settings ─────────────────────────────────────────────────────────
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openrouter")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "nvidia/llama-3.1-nemotron-ultra-253b-v1:free")
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "4096"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.0"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "2"))

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins, e.g.:
    #   http://localhost:5173,https://verifai.example.com
    CORS_ALLOWED_ORIGINS: str = os.getenv(
        "CORS_ALLOWED_ORIGINS", "http://localhost:5173"
    )


settings = Settings()
