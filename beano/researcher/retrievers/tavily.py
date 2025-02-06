import logging
from typing import List

from tavily import TavilyClient

from .retrievers import RetrieverResult, RetrieverService, RetrieverType

logger = logging.getLogger(__name__)


class TavilySearchService(RetrieverService):
    def __init__(self, access_key):
        self.client = TavilyClient(api_key=access_key)
        self.require_scraping = False
        super().__init__(RetrieverType.TAVILY)

    def search(self, query, **kwargs) -> List[RetrieverResult]:
        logger.debug(f"Using Tavily retriever for {query}")
        logger.debug(f"Using kwargs: {kwargs}")
        response = self.client.search(query=query, **kwargs)

        logger.debug(f"Response: {response}")

        research_results = []
        for result in response["results"]:
            research_results.append(
                RetrieverResult(
                    title=result["title"],
                    url=result["url"],
                    content=result["content"],
                    retriever=RetrieverType.TAVILY,
                    require_scraping=self.require_scraping,
                )
            )
        return research_results


class TavilyServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, tavily_access_key, **_ignored):
        if not self._instance:
            self._instance = TavilySearchService(tavily_access_key)
        return self._instance
