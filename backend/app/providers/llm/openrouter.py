import json
import re
from typing import Any, Dict

import httpx

from app.config import settings
from app.services.exceptions import ConfigurationError, JSONParseError, LLMError
from app.providers.llm.base import LLMProvider

_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers that some models emit."""
    text = text.strip()
    match = re.match(r"^```(?:json)?\s*([\s\S]*?)```\s*$", text)
    if match:
        return match.group(1).strip()
    return text

class OpenRouterProvider:
    """
    OpenRouter implementation of the LLMProvider interface.
    """
    def __init__(self) -> None:
        if not settings.OPENROUTER_API_KEY:
            raise ConfigurationError("OPENROUTER_API_KEY is not configured.")
        self._headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://verifai.app",
            "X-Title": "VerifAI",
        }

    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        payload = {
            "model": settings.LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": settings.MAX_TOKENS,
            "temperature": settings.TEMPERATURE,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as http:
                response = await http.post(
                    _OPENROUTER_URL,
                    headers=self._headers,
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise LLMError(f"OpenRouter API failed: {e}") from e
        except httpx.RequestError as e:
            raise LLMError(f"OpenRouter request error: {e}") from e

        data = response.json()
        text_response = data["choices"][0]["message"]["content"]
        text_response = _strip_markdown_fences(text_response)

        try:
            parsed = json.loads(text_response)
            if not isinstance(parsed, dict):
                raise JSONParseError("Parsed JSON is not a dictionary.")
            return parsed
        except json.JSONDecodeError as e:
            raise JSONParseError(f"Failed to parse JSON: {e}") from e
