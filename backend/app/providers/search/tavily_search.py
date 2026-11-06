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
        response = await asyncio.wait_for(
            self.client.search(
                query=query,
                max_results=max_results,
                include_answer=False,
                include_raw_content=False,
            ),
            timeout=30.0,
        )

        results = []
        for item in response.get("results", []):
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            title = item.get("title")
            content = item.get("content", "")
            if (
                isinstance(url, str) and url.strip()
                and isinstance(title, str) and title.strip()
                and isinstance(content, str)
            ):
                results.append(
                    SearchResult(
                        url=url.strip(),
                        title=title.strip(),
                        content=content.strip(),
                    )
                )
        return results

    async def search_multiple(self, queries: List[str], max_results: int = 5) -> List[SearchResult]:
        if not queries:
            return []

        results_lists = await asyncio.gather(
            *(self._search(query, max_results) for query in queries),
            return_exceptions=True,
        )
        failures = [result for result in results_lists if isinstance(result, BaseException)]
        successful_results = [result for result in results_lists if isinstance(result, list)]

        if failures and not successful_results:
            raise RuntimeError(
                f"All {len(queries)} Tavily search requests failed."
            ) from failures[0]

        return [item for result_list in successful_results for item in result_list]
