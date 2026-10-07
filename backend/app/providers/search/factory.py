from app.providers.search.base import SearchProvider
from app.providers.search.tavily_search import TavilySearchProvider

def get_search_provider() -> SearchProvider:
    """
    Factory function to get the current production SearchProvider.
    """
    return TavilySearchProvider()
