import logging
from typing import List, Sequence

from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document

from beano.researcher.retrievers.retrievers import RetrieverResults

logger = logging.getLogger(__name__)


class WebLoader:
    def __init__(self):
        self.scraped_urls: dict[str, Document] = {}

    def scrape_urls(self, urls: Sequence[str]) -> List[Document]:
        """
        Scrape content from the provided URLs.

        Args:
            urls (Sequence[str]): Collection of URLs to scrape.

        Returns:
            List[Document]: List of Document objects containing scraped content.
        """

        try:
            loader = WebBaseLoader(urls)
            docs = loader.load()

            return docs

        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            raise

    def load_search_result(self, search_results: RetrieverResults) -> List[Document]:
        """
        Crawl URLs and return their documents, avoiding re-crawling of previously visited URLs.

        Args:
            urls (List[str]): List of URLs to crawl

        Returns:
            List[Document]: List of documents from both newly crawled and cached URLs
        """

        urls = search_results.urls()

        # Get new URLs that haven't been crawled yet
        new_urls = [url for url in urls if url not in self.scraped_urls]
        num_new_documents = 0
        documents = []
        new_urls_to_scrape = []
        # Add cached documents for previously crawled URLs
        cached_documents = [
            self.scraped_urls[url] for url in urls if url in self.scraped_urls
        ]
        documents.extend(cached_documents)

        for r in search_results.results:
            if r.url not in self.scraped_urls:
                num_new_documents += 1
                if r.require_scraping == True:
                    new_urls_to_scrape.append(r.url)
                else:
                    doc = Document(
                        page_content=r.content,
                        metadata={"source": r.url, "title": r.title},
                    )
                    documents.append(doc)
                    self.scraped_urls[r.url] = doc

        # Crawl new URLs if any exist
        if new_urls_to_scrape:

            logger.debug(f"New URLs to crawl: {new_urls_to_scrape}")
            new_documents = self.scrape_urls(new_urls_to_scrape)
            # Cache the newly crawled documents
            for doc in new_documents:
                source_url = doc.metadata["source"]
                logger.debug(f"Caching document from {source_url}")
                self.scraped_urls[source_url] = doc
            documents.extend(new_documents)

        return documents, num_new_documents, len(cached_documents)
