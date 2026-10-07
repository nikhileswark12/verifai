from app.providers.llm.base import LLMProvider
from app.providers.llm.openrouter import OpenRouterProvider

def get_llm_provider() -> LLMProvider:
    """
    Factory function to get the current production LLMProvider.
    """
    return OpenRouterProvider()
