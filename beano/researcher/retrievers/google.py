import logging
from typing import List

from googlesearch import search

from beano.utils import exponential_backoff_retry

from .retrievers import RetrieverResult, RetrieverService, RetrieverType

logger = logging.getLogger(__name__)


class GoogleSearchService(RetrieverService):
    def __init__(self):
        self.require_scraping = True
        super().__init__(RetrieverType.GOOGLE)

    @exponential_backoff_retry(Exception)
    def search(self, query, max_results=20) -> List[RetrieverResult]:
        logger.debug(f"Using Google retriever for {query}")
        response = search(query, advanced=True, num_results=max_results)

        research_results = []
        for result in response:

            research_results.append(
                RetrieverResult(
                    title=result.title,
                    url=result.url,
                    content=result.description,
                    retriever=RetrieverType.GOOGLE,
                    require_scraping=self.require_scraping,
                )
            )
        return research_results


class GoogleServiceBuilder:
    def __init__(self):
        self._instance = None

    def __call__(self, **_ignored):
        if not self._instance:
            self._instance = GoogleSearchService()
        return self._instance
