import asyncio
import logging

from langchain_core.runnables import RunnableConfig

from ..model import SectionState, Source
from ..utils import format_web_search
from ..web_search import WebSearch

logger = logging.getLogger(__name__)


class SectionWebResearcher:
    """Search the web for each query, then return a list of raw sources and a formatted string of sources."""

    N = "section_search_web"

    def __init__(self, web_search: WebSearch):
        self.web_search = web_search

    def __call__(self, state: SectionState, config: RunnableConfig):
        """Search the web for each query, then return a list of raw sources and a formatted string of sources."""

        # Get state
        search_queries = state["search_queries"]

        # Web search
        try:
            logger.debug(f"Search Queries: {search_queries}")

            search_results = asyncio.run(
                self.web_search.search(search_queries))

            source_str = format_web_search(
                search_results, max_tokens_per_source=5000, include_raw_content=False
            )

            sources = []

            for search_result in search_results:
                sources.append(
                    Source(title=search_result["title"],
                           url=search_result["url"])
                )

        except Exception as e:
            logger.error(f"Error searching web: {e}")
            source_str = ""

        return {
            "source_str": source_str,
            "sources": sources,
            "search_iterations": state["search_iterations"] + 1,
        }
