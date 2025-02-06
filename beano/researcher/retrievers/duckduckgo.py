import logging
from typing import List

from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import RatelimitException

from beano.utils import exponential_backoff_retry

from .retrievers import RetrieverResult, RetrieverService, RetrieverType

logger = logging.getLogger(__name__)


class DuckDuckGoSearchService(RetrieverService):
    def __init__(self):
        self.require_scraping = True
        super().__init__(RetrieverType.DUCK)

    @exponential_backoff_retry(RatelimitException)
    def search(self, query, **kwargs) -> List[RetrieverResult]:
        self.client = DDGS()
        logger.debug(f"Using DuckDuckGo retriever for {query}")
        response = self.client.text(query, **kwargs)
        logger.debug(f"DuckDuckGo response: {response}")

        research_results = []
        for result in response:
            research_results.append(
                RetrieverResult(
                    title=result["title"],
                    url=result["href"],
                    content=result["body"],
                    retriever=RetrieverType.DUCK,
                    require_scraping=self.require_scraping,
                )
            )
        return research_results


class DuckDuckGoServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, **_ignored):
        if not self._instance:
            self._instance = DuckDuckGoSearchService()
        return self._instance
