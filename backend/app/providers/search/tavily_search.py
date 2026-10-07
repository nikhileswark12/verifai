import asyncio
from typing import List

from tavily import AsyncTavilyClient

from app.config import settings
from app.services.exceptions import ConfigurationError
from app.providers.search.base import SearchProvider, SearchResult

class TavilySearchProvider:
    """
    Tavily implementation of the SearchProvider interface.
    """
    def __init__(self) -> None:
        if not settings.TAVILY_API_KEY:
            raise ConfigurationError("TAVILY_API_KEY is not configured.")
        self.client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

    async def _search(self, query: str, max_results: int) -> List[SearchResult]:
        try:
            response = await asyncio.wait_for(
                self.client.search(
                    query=query,
                    max_results=max_results,
                    include_answer=False,
                    include_raw_content=False,
                ),
                timeout=30.0
            )
            
            results = []
            for item in response.get("results", []):
                if isinstance(item, dict):
                    url = item.get("url")
                    title = item.get("title")
                    content = item.get("content", "")
                    if url and isinstance(url, str) and url.strip() and title and isinstance(title, str) and title.strip():
                        results.append(
                            SearchResult(
                                url=url.strip(),
                                title=title.strip(),
                                content=content.strip()
                            )
                        )
            return results
        except Exception:
            return []

    async def search_multiple(self, queries: List[str], max_results: int = 5) -> List[SearchResult]:
        tasks = [self._search(q, max_results) for q in queries]
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_results = []
        for res in results_lists:
            if isinstance(res, list):
                all_results.extend(res)
        return all_results
