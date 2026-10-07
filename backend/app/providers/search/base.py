from dataclasses import dataclass
from typing import List, Protocol

@dataclass
class SearchResult:
    url: str
    title: str
    content: str

class SearchProvider(Protocol):
    async def search_multiple(self, queries: List[str], max_results: int = 5) -> List[SearchResult]:
        """
        Perform multiple searches and return a combined list of SearchResults.
        """
        ...
