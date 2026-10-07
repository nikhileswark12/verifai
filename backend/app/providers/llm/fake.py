from typing import Any, Dict
from app.providers.llm.base import LLMProvider

class FakeLLMProvider:
    """
    A fake LLMProvider for testing.
    Always returns the provided JSON response.
    """
    def __init__(self, response: Dict[str, Any] = None):
        self.response = response or {}

    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        return self.response
