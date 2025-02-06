import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Sequence, Tuple

from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document

from beano.researcher.retrievers.retrievers import (RetrieverResult,
                                                    RetrieverResults)

logger = logging.getLogger(__name__)


@dataclass
class CachedDocument:
    """Represents a cached document with timestamp for TTL functionality"""

    document: Document
    timestamp: datetime
    ttl: timedelta = timedelta(hours=24)

    def is_expired(self) -> bool:
        """Check if the cached document has expired"""
        return datetime.now() - self.timestamp > self.ttl


class WebLoaderError(Exception):
    """Custom exception for WebLoader errors"""

    pass


class WebLoader:
    """Handles web content loading and caching from URLs"""

    def __init__(self, cache_ttl_hours: int = 24, max_workers: int = 5):
        """
        Initialize WebLoader with configuration parameters.

        Args:
            cache_ttl_hours (int): Time-to-live for cached documents in hours
            max_workers (int): Maximum number of concurrent workers for scraping
        """
        self._cache: Dict[str, CachedDocument] = {}
        self._cache_ttl = timedelta(hours=cache_ttl_hours)
        self._max_workers = max_workers

    def _create_document(self, result: RetrieverResult) -> Document:
        """Create a Document object from a SearchResult"""
        return Document(
            page_content=result.content,
            metadata={"source": result.url, "title": result.title},
        )

    def _scrape_single_url(self, url: str) -> Document:
        """
        Scrape content from a single URL.

        Args:
            url (str): URL to scrape

        Returns:
            Document: Scraped content as a Document object

        Raises:
            WebLoaderError: If scraping fails
        """
        try:
            loader = WebBaseLoader([url])
            docs = loader.load()
            return docs[0] if docs else None
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")
            raise WebLoaderError(f"Failed to scrape {url}: {str(e)}")

    def _batch_scrape_urls(self, urls: List[str]) -> List[Document]:
        """
        Scrape multiple URLs concurrently.

        Args:
            urls (List[str]): List of URLs to scrape

        Returns:
            List[Document]: List of scraped documents
        """
        documents = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_to_url = {
                executor.submit(self._scrape_single_url, url): url for url in urls
            }

            for future in future_to_url:
                url = future_to_url[future]
                try:
                    doc = future.result()
                    if doc:
                        documents.append(doc)
                except WebLoaderError as e:
                    logger.error(f"Failed to scrape {url}: {str(e)}")
                    continue

        return documents

    def _get_cached_document(self, url: str) -> Document | None:
        """
        Retrieve a document from cache if it exists and hasn't expired.

        Args:
            url (str): URL of the document

        Returns:
            Document | None: Cached document or None if not found/expired
        """
        cached = self._cache.get(url)
        if cached and not cached.is_expired():
            return cached.document
        if cached:
            del self._cache[url]
        return None

    def _cache_document(self, url: str, document: Document) -> None:
        """
        Cache a document with its URL.

        Args:
            url (str): URL of the document
            document (Document): Document to cache
        """
        self._cache[url] = CachedDocument(
            document=document, timestamp=datetime.now(), ttl=self._cache_ttl
        )

    def load_search_result(
        self, search_results: RetrieverResults
    ) -> Tuple[List[Document], int, int]:
        """
        Process search results and return documents, handling caching and scraping as needed.

        Args:
            search_results (RetrieverResults): Search results to process

        Returns:
            Tuple[List[Document], int, int]:
                - List of documents
                - Number of new documents
                - Number of cached documents
        """
        documents: List[Document] = []
        urls_to_scrape: List[str] = []
        new_document_count = 0
        cached_document_count = 0
        logger.info(f"load_search_result {search_results}")

        # Process each search result
        for result in search_results.results:
            logger.info(f"Processing search result: {result.url}")
            # Check cache first
            cached_doc = self._get_cached_document(result.url)
            if cached_doc:
                logger.info(f"Using cached document for URL: {result.url}")

                documents.append(cached_doc)
                cached_document_count += 1
                continue

            new_document_count += 1
            if result.require_scraping:
                urls_to_scrape.append(result.url)
            else:
                logger.info(
                    f"Loading document from retriever result: {result.url}")
                doc = self._create_document(result)
                documents.append(doc)
                self._cache_document(result.url, doc)

        # Handle URLs that need scraping
        if urls_to_scrape:
            logger.info(f"Scraping {len(urls_to_scrape)} new URLs")
            scraped_docs = self._batch_scrape_urls(urls_to_scrape)

            for doc in scraped_docs:
                source_url = doc.metadata["source"]
                self._cache_document(source_url, doc)
                documents.append(doc)

        return documents, new_document_count, cached_document_count

    def clear_cache(self) -> None:
        """Clear the document cache"""
        self._cache.clear()

    def remove_expired_cache(self) -> int:
        """
        Remove expired items from cache.

        Returns:
            int: Number of items removed
        """
        initial_size = len(self._cache)
        self._cache = {
            url: cached
            for url, cached in self._cache.items()
            if not cached.is_expired()
        }
        return initial_size - len(self._cache)
