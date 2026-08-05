import asyncio
from typing import Any, Dict, List

from tavily import AsyncTavilyClient

from app.config import settings
from app.services.exceptions import ConfigurationError


class TavilyClient:
    def __init__(self) -> None:
        # TAVILY_API_KEY is validated at startup via Settings._require().
        # If we reach here it is guaranteed to be non-empty.
        if not settings.TAVILY_API_KEY:
            raise ConfigurationError("TAVILY_API_KEY is not configured.")
        self.client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

    async def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        try:
            response = await self.client.search(
                query=query,
                max_results=max_results,
                include_answer=False,
                include_raw_content=False,
            )
            return response.get("results", [])
        except Exception:
            return []

    async def search_multiple(self, queries: List[str], max_results: int = 5) -> List[Dict[str, Any]]:
        tasks = [self.search(q, max_results) for q in queries]
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results = []
        for res in results_lists:
            if isinstance(res, list):
                all_results.extend(res)
        return all_results
