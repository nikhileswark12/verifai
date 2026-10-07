from typing import List
from app.providers.search.base import SearchProvider, SearchResult

class FakeSearchProvider:
    """
    A fake SearchProvider for testing.
    Always returns the provided search results.
    """
    def __init__(self, results: List[SearchResult] = None):
        self.results = results or []

    async def search_multiple(self, queries: List[str], max_results: int = 5) -> List[SearchResult]:
        return self.results
