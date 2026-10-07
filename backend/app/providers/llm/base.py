from typing import Any, Dict, Protocol

class LLMProvider(Protocol):
    async def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Generate a structured JSON response from the LLM.
        """
        ...
