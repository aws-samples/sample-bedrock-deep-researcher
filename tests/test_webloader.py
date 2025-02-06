from beano.researcher.retrievers.retrievers import RetrieverResult
from beano.researcher.retrievers.retrievers import RetrieverResult, RetrieverResults
from beano.researcher.retrievers.retrievers import RetrieverResults, RetrieverResult
from beano.researcher.webloader import CachedDocument
from beano.researcher.webloader import WebLoader
from beano.researcher.webloader import WebLoader, CachedDocument
from beano.researcher.webloader import WebLoader, Document
from beano.researcher.webloader import WebLoader, WebLoaderError
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from datetime import timedelta
from langchain_core.documents import Document
from typing import List
from typing import List, Tuple
from unittest.mock import MagicMock
from unittest.mock import MagicMock, patch
from unittest.mock import Mock
from unittest.mock import Mock, patch
from unittest.mock import patch, MagicMock
import pytest
import threading
import time


class TestWebloader:
    def test__batch_scrape_urls_2(self):
        """
        Test _batch_scrape_urls when no documents are returned from scraping.
        """
        # Initialize WebLoader
        web_loader = WebLoader(max_workers=2)

        # Mock URLs
        urls = ["http://example1.com", "http://example2.com"]

        # Mock _scrape_single_url to return None for all URLs
        with patch.object(WebLoader, "_scrape_single_url", return_value=None):
            result = web_loader._batch_scrape_urls(urls)

        # Assertions
        assert len(result) == 0  # No documents should be returned
        assert isinstance(result, list)

    def test__batch_scrape_urls_empty_list(self):
        """
        Test _batch_scrape_urls method with an empty list of URLs.
        """
        # Initialize WebLoader
        web_loader = WebLoader()

        # Call the method with an empty list
        result = web_loader._batch_scrape_urls([])

        # Assertions
        assert result == []

    def test__batch_scrape_urls_exception_handling(self):
        """
        Test exception handling in _batch_scrape_urls.
        """
        webloader = WebLoader()
        urls = ["http://example1.com", "http://example2.com"]

        with patch("beano.researcher.webloader.WebBaseLoader") as mock_loader:
            mock_loader.return_value.load.side_effect = [
                WebLoaderError("Failed to scrape"),
                [
                    Document(
                        page_content="Content",
                        metadata={"source": "http://example2.com"},
                    )
                ],
            ]

            result = webloader._batch_scrape_urls(urls)

        assert len(result) == 1, "Expected one successful document"
        assert result[0].metadata["source"] == "http://example2.com"

    def test__batch_scrape_urls_max_workers(self):
        """
        Test _batch_scrape_urls method respects the max_workers limit.
        """
        # Initialize WebLoader with max_workers=1
        web_loader = WebLoader(max_workers=1)

        # Mock URLs
        urls = ["http://example1.com", "http://example2.com"]

        # Mock ThreadPoolExecutor
        with patch(
            "beano.researcher.webloader.ThreadPoolExecutor", wraps=ThreadPoolExecutor
        ) as mock_executor:
            # Mock _scrape_single_url method
            with patch.object(WebLoader, "_scrape_single_url") as mock_scrape:
                mock_scrape.return_value = Document(
                    page_content="Content", metadata={"source": "http://example.com"}
                )

                # Call the method
                web_loader._batch_scrape_urls(urls)

            # Assert that ThreadPoolExecutor was called with max_workers=1
            mock_executor.assert_called_once_with(max_workers=1)

    def test__batch_scrape_urls_max_workers_limit(self):
        """
        Test _batch_scrape_urls respects the max_workers limit.
        """
        max_workers = 3
        webloader = WebLoader(max_workers=max_workers)
        urls = [f"http://example{i}.com" for i in range(10)]

        with patch(
            "beano.researcher.webloader.ThreadPoolExecutor", autospec=True
        ) as mock_executor:
            webloader._batch_scrape_urls(urls)

            mock_executor.assert_called_once_with(max_workers=max_workers)

    def test__batch_scrape_urls_successful_scraping(self):
        """
        Test _batch_scrape_urls method when all URLs are successfully scraped.
        """
        # Initialize WebLoader
        web_loader = WebLoader(max_workers=2)

        # Mock URLs
        urls = ["http://example1.com", "http://example2.com"]

        # Mock _scrape_single_url method
        with patch.object(WebLoader, "_scrape_single_url") as mock_scrape:
            mock_scrape.side_effect = [
                Document(
                    page_content="Content 1", metadata={"source": "http://example1.com"}
                ),
                Document(
                    page_content="Content 2", metadata={"source": "http://example2.com"}
                ),
            ]

            # Call the method
            result = web_loader._batch_scrape_urls(urls)

        # Assertions
        assert len(result) == 2
        assert all(isinstance(doc, Document) for doc in result)
        assert result[0].page_content == "Content 1"
        assert result[1].page_content == "Content 2"
        assert mock_scrape.call_count == 2

    def test__batch_scrape_urls_with_empty_input(self):
        """
        Test _batch_scrape_urls with an empty list of URLs.
        """
        webloader = WebLoader()
        result = webloader._batch_scrape_urls([])
        assert result == [], "Expected an empty list when input is empty"

    def test__batch_scrape_urls_with_errors(self):
        """
        Test _batch_scrape_urls method when some URLs fail to scrape.
        """
        # Initialize WebLoader
        web_loader = WebLoader(max_workers=2)

        # Mock URLs
        urls = ["http://example1.com", "http://example2.com", "http://example3.com"]

        # Mock _scrape_single_url method
        with patch.object(WebLoader, "_scrape_single_url") as mock_scrape:
            mock_scrape.side_effect = [
                Document(
                    page_content="Content 1", metadata={"source": "http://example1.com"}
                ),
                WebLoaderError("Failed to scrape"),
                Document(
                    page_content="Content 3", metadata={"source": "http://example3.com"}
                ),
            ]

            # Call the method
            result = web_loader._batch_scrape_urls(urls)

        # Assertions
        assert len(result) == 2
        assert all(isinstance(doc, Document) for doc in result)
        assert result[0].page_content == "Content 1"
        assert result[1].page_content == "Content 3"
        assert mock_scrape.call_count == 3

    def test__batch_scrape_urls_with_incorrect_input_type(self):
        """
        Test _batch_scrape_urls with incorrect input type.
        """
        webloader = WebLoader()
        with pytest.raises(TypeError):
            webloader._batch_scrape_urls("http://example.com")

    def test__batch_scrape_urls_with_invalid_urls(self):
        """
        Test _batch_scrape_urls with invalid URLs.
        """
        webloader = WebLoader()
        invalid_urls = ["not_a_url", "http://", "ftp://invalid.com"]

        with patch("beano.researcher.webloader.WebBaseLoader") as mock_loader:
            mock_loader.return_value.load.side_effect = WebLoaderError("Invalid URL")
            result = webloader._batch_scrape_urls(invalid_urls)

        assert result == [], "Expected an empty list when all URLs are invalid"

    def test__batch_scrape_urls_with_mixed_results(self):
        """
        Test _batch_scrape_urls with a mix of successful and failed scrapes.
        """
        webloader = WebLoader()
        urls = ["http://success1.com", "http://fail.com", "http://success2.com"]

        with patch("beano.researcher.webloader.WebBaseLoader") as mock_loader:
            mock_loader.return_value.load.side_effect = [
                [
                    Document(
                        page_content="Content 1",
                        metadata={"source": "http://success1.com"},
                    )
                ],
                WebLoaderError("Failed to scrape"),
                [
                    Document(
                        page_content="Content 2",
                        metadata={"source": "http://success2.com"},
                    )
                ],
            ]

            result = webloader._batch_scrape_urls(urls)

        assert len(result) == 2, "Expected two successful documents"
        assert [doc.metadata["source"] for doc in result] == [
            "http://success1.com",
            "http://success2.com",
        ]

    def test__cache_document_max_cache_size(self):
        """
        Test _cache_document with a large number of documents to check if there's any size limit.
        """
        loader = WebLoader()
        document = Document(page_content="Test content")

        for i in range(10000):  # Try to cache 10000 documents
            url = f"https://example.com/{i}"
            loader._cache_document(url, document)

        assert len(loader._cache) == 10000

    def test__cache_document_overwrite_existing(self):
        """
        Test _cache_document overwriting an existing cached document.
        """
        loader = WebLoader()
        url = "https://example.com"
        original_document = Document(page_content="Original content")
        new_document = Document(page_content="New content")

        loader._cache_document(url, original_document)
        original_timestamp = loader._cache[url].timestamp

        # Wait a moment to ensure a different timestamp
        time.sleep(0.01)

        loader._cache_document(url, new_document)

        assert loader._cache[url].document == new_document
        assert loader._cache[url].timestamp > original_timestamp

    def test__cache_document_with_empty_url(self):
        """
        Test _cache_document with an empty URL.
        """
        loader = WebLoader()
        document = Document(page_content="Test content")

        with pytest.raises(ValueError):
            loader._cache_document("", document)

    def test__cache_document_with_expired_ttl(self):
        """
        Test _cache_document with an expired TTL.
        """
        loader = WebLoader(cache_ttl_hours=0)  # Set TTL to 0 hours
        document = Document(page_content="Test content")
        url = "https://example.com"

        loader._cache_document(url, document)

        assert url in loader._cache
        assert loader._cache[url].is_expired()

    def test__cache_document_with_extremely_long_url(self):
        """
        Test _cache_document with an extremely long URL.
        """
        loader = WebLoader()
        document = Document(page_content="Test content")
        long_url = "https://example.com/" + "a" * 2000  # Creating a very long URL

        loader._cache_document(long_url, document)
        assert long_url in loader._cache

    def test__cache_document_with_invalid_document_type(self):
        """
        Test _cache_document with an invalid document type.
        """
        loader = WebLoader()
        invalid_document = "This is not a Document object"

        with pytest.raises(TypeError):
            loader._cache_document("https://example.com", invalid_document)

    def test__cache_document_with_none_document(self):
        """
        Test _cache_document with None as document.
        """
        loader = WebLoader()

        with pytest.raises(TypeError):
            loader._cache_document("https://example.com", None)

    def test__cache_document_with_none_url(self):
        """
        Test _cache_document with None as URL.
        """
        loader = WebLoader()
        document = Document(page_content="Test content")

        with pytest.raises(TypeError):
            loader._cache_document(None, document)

    def test__get_cached_document_1(self):
        """
        Test that _get_cached_document returns None for an expired cached document and removes it from cache.
        """
        # Initialize WebLoader
        web_loader = WebLoader()

        # Create a mock document and expired CachedDocument
        mock_document = Document(
            page_content="Test content", metadata={"source": "http://expired.com"}
        )
        mock_cached_document = CachedDocument(
            document=mock_document,
            timestamp=datetime.now() - timedelta(hours=25),  # Expired
            ttl=timedelta(hours=24),
        )

        # Set up the cache with the expired mock entry
        web_loader._cache = {"http://expired.com": mock_cached_document}

        # Call the method under test
        result = web_loader._get_cached_document("http://expired.com")

        # Assert that the result is None
        assert result is None

        # Assert that the expired document has been removed from the cache
        assert "http://expired.com" not in web_loader._cache

    def test__get_cached_document_expired_cache(self):
        """
        Test _get_cached_document when the cached document has expired.
        """
        # Initialize WebLoader
        web_loader = WebLoader()

        # Create a mock document
        mock_document = Document(
            page_content="Test content", metadata={"source": "http://example.com"}
        )

        # Create an expired CachedDocument
        expired_cache = CachedDocument(
            document=mock_document,
            timestamp=datetime.now() - timedelta(hours=25),  # Expired
            ttl=timedelta(hours=24),
        )

        # Set up the cache
        url = "http://example.com"
        web_loader._cache = {url: expired_cache}

        # Call the method
        result = web_loader._get_cached_document(url)

        # Assert that the result is None
        assert result is None

        # Assert that the expired document was removed from the cache
        assert url not in web_loader._cache

    def test__get_cached_document_with_empty_url(self):
        """Test _get_cached_document with an empty URL string"""
        webloader = WebLoader()
        result = webloader._get_cached_document("")
        assert result is None

    def test__get_cached_document_with_expired_cache(self):
        """Test _get_cached_document with an expired cached document"""
        webloader = WebLoader()
        url = "https://example.com"
        expired_doc = CachedDocument(
            document=Document(page_content="Test content"),
            timestamp=datetime.now() - timedelta(hours=25),
            ttl=timedelta(hours=24),
        )
        webloader._cache[url] = expired_doc

        result = webloader._get_cached_document(url)
        assert result is None
        assert url not in webloader._cache

    def test__get_cached_document_with_modified_cache_ttl(self):
        """Test _get_cached_document with a modified cache TTL"""
        webloader = WebLoader(cache_ttl_hours=1)
        url = "https://example.com"
        doc = Document(page_content="Test content")
        cached_doc = CachedDocument(
            document=doc,
            timestamp=datetime.now() - timedelta(minutes=59),
            ttl=timedelta(hours=1),
        )
        webloader._cache[url] = cached_doc

        result = webloader._get_cached_document(url)
        assert result == doc

        # Check after TTL has expired
        cached_doc.timestamp = datetime.now() - timedelta(hours=2)
        result = webloader._get_cached_document(url)
        assert result is None
        assert url not in webloader._cache

    def test__get_cached_document_with_non_existent_url(self):
        """Test _get_cached_document with a URL that doesn't exist in the cache"""
        webloader = WebLoader()
        result = webloader._get_cached_document("https://nonexistent.com")
        assert result is None

    def test__get_cached_document_with_non_string_url(self):
        """Test _get_cached_document with a non-string URL"""
        webloader = WebLoader()
        with pytest.raises(AttributeError):
            webloader._get_cached_document(123)

    @patch("beano.researcher.webloader.WebBaseLoader")
    def test__scrape_single_url_empty_result(self, mock_web_base_loader):
        """
        Test _scrape_single_url when WebBaseLoader returns an empty list.
        """
        mock_web_base_loader.return_value.load.return_value = []

        loader = WebLoader()
        result = loader._scrape_single_url("http://example.com")
        assert result is None

    @patch("beano.researcher.webloader.WebBaseLoader")
    def test__scrape_single_url_exception_handling(self, mock_web_base_loader):
        """
        Test exception handling in _scrape_single_url when WebBaseLoader raises an exception.
        """
        mock_web_base_loader.return_value.load.side_effect = Exception(
            "Scraping failed"
        )

        loader = WebLoader()
        with pytest.raises(
            WebLoaderError, match="Failed to scrape http://example.com: Scraping failed"
        ):
            loader._scrape_single_url("http://example.com")

    def test__scrape_single_url_with_empty_url(self):
        """
        Test _scrape_single_url with an empty URL string.
        """
        loader = WebLoader()
        with pytest.raises(WebLoaderError):
            loader._scrape_single_url("")

    def test__scrape_single_url_with_incorrect_type(self):
        """
        Test _scrape_single_url with an incorrect input type.
        """
        loader = WebLoader()
        with pytest.raises(TypeError):
            loader._scrape_single_url(123)

    def test__scrape_single_url_with_invalid_url(self):
        """
        Test _scrape_single_url with an invalid URL.
        """
        loader = WebLoader()
        with pytest.raises(WebLoaderError):
            loader._scrape_single_url("not_a_valid_url")

    @patch("beano.researcher.webloader.WebBaseLoader")
    def test__scrape_single_url_with_very_long_url(self, mock_web_base_loader):
        """
        Test _scrape_single_url with a very long URL to check for any length-related issues.
        """
        very_long_url = (
            "http://example.com/" + "a" * 2000
        )  # URL with 2000 'a' characters
        mock_web_base_loader.return_value.load.return_value = [
            Document(page_content="content", metadata={})
        ]

        loader = WebLoader()
        result = loader._scrape_single_url(very_long_url)
        assert isinstance(result, Document)
        mock_web_base_loader.assert_called_once_with([very_long_url])

    def test_batch_scrape_urls_with_failed_scraping(self):
        """
        Test _batch_scrape_urls when scraping fails for some URLs.
        """
        # Initialize WebLoader
        web_loader = WebLoader(max_workers=2)

        # Mock URLs
        urls = ["http://example1.com", "http://example2.com", "http://example3.com"]

        # Mock _scrape_single_url to simulate failed scraping
        def mock_scrape_single_url(url):
            if url == "http://example2.com":
                raise WebLoaderError("Simulated scraping error")
            return Document(
                page_content=f"Content from {url}", metadata={"source": url}
            )

        with patch.object(
            WebLoader, "_scrape_single_url", side_effect=mock_scrape_single_url
        ):
            with patch("beano.researcher.webloader.logger.error") as mock_logger:
                result = web_loader._batch_scrape_urls(urls)

        # Assertions
        assert len(result) == 2  # Two successful scrapes out of three URLs
        assert all(isinstance(doc, Document) for doc in result)
        assert [doc.metadata["source"] for doc in result] == [
            "http://example1.com",
            "http://example3.com",
        ]
        mock_logger.assert_called_once_with(
            "Failed to scrape http://example2.com: Simulated scraping error"
        )

    def test_cache_document_stores_correctly(self):
        """
        Test that _cache_document correctly stores a document in the cache
        """
        # Initialize WebLoader
        web_loader = WebLoader(cache_ttl_hours=24)

        # Create a test document
        test_url = "https://example.com"
        test_document = Document(
            page_content="Test content", metadata={"source": test_url}
        )

        # Call the method under test
        web_loader._cache_document(test_url, test_document)

        # Assert that the document is stored in the cache
        assert test_url in web_loader._cache
        cached_doc = web_loader._cache[test_url]

        # Assert the properties of the cached document
        assert isinstance(cached_doc, CachedDocument)
        assert cached_doc.document == test_document
        assert isinstance(cached_doc.timestamp, datetime)
        assert cached_doc.ttl == timedelta(hours=24)

        # Assert that the timestamp is recent (within the last second)
        assert (datetime.now() - cached_doc.timestamp).total_seconds() < 1

    def test_clear_cache_clears_all_documents(self):
        """
        Test that clear_cache method removes all documents from the cache
        """
        # Initialize WebLoader
        web_loader = WebLoader()

        # Add some documents to the cache
        doc1 = Document(
            page_content="Test content 1", metadata={"source": "http://example1.com"}
        )
        doc2 = Document(
            page_content="Test content 2", metadata={"source": "http://example2.com"}
        )

        web_loader._cache = {
            "http://example1.com": CachedDocument(
                document=doc1, timestamp=datetime.now()
            ),
            "http://example2.com": CachedDocument(
                document=doc2, timestamp=datetime.now()
            ),
        }

        # Verify that the cache is not empty
        assert len(web_loader._cache) == 2

        # Call the clear_cache method
        web_loader.clear_cache()

        # Verify that the cache is now empty
        assert len(web_loader._cache) == 0

    def test_clear_cache_does_not_affect_other_attributes(self):
        """
        Test that clear_cache only affects the cache and not other attributes.
        """
        loader = WebLoader(cache_ttl_hours=48, max_workers=10)
        initial_ttl = loader._cache_ttl
        initial_max_workers = loader._max_workers

        loader.clear_cache()

        assert loader._cache_ttl == initial_ttl
        assert loader._max_workers == initial_max_workers

    def test_clear_cache_empty_cache(self):
        """
        Test clearing an empty cache.
        """
        loader = WebLoader()
        initial_cache_size = len(loader._cache)
        loader.clear_cache()
        assert len(loader._cache) == 0
        assert initial_cache_size == len(loader._cache)

    def test_clear_cache_multiple_calls(self):
        """
        Test calling clear_cache multiple times.
        """
        loader = WebLoader()
        # Add an item to the cache
        loader._cache_document(
            "http://example.com",
            Document(
                page_content="Example content",
                metadata={"source": "http://example.com"},
            ),
        )

        loader.clear_cache()
        assert len(loader._cache) == 0

        # Call clear_cache again on an empty cache
        loader.clear_cache()
        assert len(loader._cache) == 0

    def test_clear_cache_thread_safety(self):
        """
        Test that clear_cache is thread-safe.
        """

        loader = WebLoader()
        # Add some items to the cache
        loader._cache_document(
            "http://example.com",
            Document(
                page_content="Example content",
                metadata={"source": "http://example.com"},
            ),
        )
        loader._cache_document(
            "http://test.com",
            Document(
                page_content="Test content", metadata={"source": "http://test.com"}
            ),
        )

        def clear_cache_thread():
            loader.clear_cache()

        threads = [threading.Thread(target=clear_cache_thread) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert len(loader._cache) == 0

    def test_clear_cache_with_items(self):
        """
        Test clearing a cache with items.
        """
        loader = WebLoader()
        # Add some items to the cache
        loader._cache_document(
            "http://example.com",
            Document(
                page_content="Example content",
                metadata={"source": "http://example.com"},
            ),
        )
        loader._cache_document(
            "http://test.com",
            Document(
                page_content="Test content", metadata={"source": "http://test.com"}
            ),
        )

        initial_cache_size = len(loader._cache)
        assert initial_cache_size > 0

        loader.clear_cache()
        assert len(loader._cache) == 0
        assert initial_cache_size != len(loader._cache)

    def test_create_document_from_retriever_result(self):
        """
        Test that _create_document correctly creates a Document from a RetrieverResult
        """
        # Arrange
        webloader = WebLoader()
        retriever_result = RetrieverResult(
            url="https://example.com",
            title="Example Page",
            content="This is the page content.",
            require_scraping=False,
        )

        # Act
        document = webloader._create_document(retriever_result)

        # Assert
        assert isinstance(document, Document)
        assert document.page_content == "This is the page content."
        assert document.metadata == {
            "source": "https://example.com",
            "title": "Example Page",
        }

    def test_create_document_with_empty_result(self):
        """
        Test _create_document with an empty RetrieverResult.
        """
        loader = WebLoader()
        empty_result = RetrieverResult(content="", url="", title="")

        document = loader._create_document(empty_result)

        assert isinstance(document, Document)
        assert document.page_content == ""
        assert document.metadata == {"source": "", "title": ""}

    def test_create_document_with_invalid_types(self):
        """
        Test _create_document with invalid types in RetrieverResult.
        """
        loader = WebLoader()
        invalid_result = RetrieverResult(content=123, url=456, title=789)

        with pytest.raises(TypeError):
            loader._create_document(invalid_result)

    def test_create_document_with_none_values(self):
        """
        Test _create_document with None values in RetrieverResult.
        """
        loader = WebLoader()
        none_result = RetrieverResult(content=None, url=None, title=None)

        with pytest.raises(TypeError):
            loader._create_document(none_result)

    def test_create_document_with_special_characters(self):
        """
        Test _create_document with special characters in content and metadata.
        """
        loader = WebLoader()
        special_result = RetrieverResult(
            content="Special chars: !@#$%^&*()",
            url="http://example.com/special?query=value&key=123",
            title='Special Title: <>?"{}|',
        )

        document = loader._create_document(special_result)

        assert isinstance(document, Document)
        assert document.page_content == "Special chars: !@#$%^&*()"
        assert document.metadata == {
            "source": "http://example.com/special?query=value&key=123",
            "title": 'Special Title: <>?"{}|',
        }

    def test_create_document_with_unicode_characters(self):
        """
        Test _create_document with Unicode characters in content and metadata.
        """
        loader = WebLoader()
        unicode_result = RetrieverResult(
            content="Unicode content: 你好世界",
            url="http://example.com/unicode",
            title="Unicode Title: こんにちは世界",
        )

        document = loader._create_document(unicode_result)

        assert isinstance(document, Document)
        assert document.page_content == "Unicode content: 你好世界"
        assert document.metadata == {
            "source": "http://example.com/unicode",
            "title": "Unicode Title: こんにちは世界",
        }

    def test_create_document_with_very_long_content(self):
        """
        Test _create_document with extremely long content.
        """
        loader = WebLoader()
        long_content = "a" * 1000000  # 1 million characters
        long_result = RetrieverResult(
            content=long_content, url="http://example.com", title="Long Content"
        )

        document = loader._create_document(long_result)

        assert isinstance(document, Document)
        assert len(document.page_content) == 1000000
        assert document.metadata == {
            "source": "http://example.com",
            "title": "Long Content",
        }

    def test_get_cached_document_expired(self):
        """
        Test _get_cached_document when the cached document has expired.
        """
        webloader = WebLoader()
        url = "https://example.com"
        document = Document(page_content="Test content", metadata={"source": url})

        # Add an expired document to the cache
        expired_time = datetime.now() - timedelta(hours=25)
        webloader._cache[url] = CachedDocument(
            document=document, timestamp=expired_time
        )

        result = webloader._get_cached_document(url)

        assert result is None
        assert len(webloader._cache) == 0

    def test_get_cached_document_non_existent(self):
        """
        Test _get_cached_document when the URL is not in the cache.
        """
        webloader = WebLoader()
        url = "https://example.com"

        # Ensure the cache is empty
        assert len(webloader._cache) == 0

        result = webloader._get_cached_document(url)

        assert result is None
        assert len(webloader._cache) == 0

    def test_get_cached_document_returns_none_for_nonexistent_url(self):
        """
        Test that _get_cached_document returns None for a URL that doesn't exist in the cache.
        """
        # Initialize WebLoader
        web_loader = WebLoader()

        # Call the method under test with a non-existent URL
        result = web_loader._get_cached_document("http://nonexistent.com")

        # Assert that the result is None
        assert result is None

    def test_get_cached_document_returns_valid_document(self):
        """
        Test that _get_cached_document returns a valid document when it exists in cache and is not expired.
        """
        # Initialize WebLoader
        web_loader = WebLoader()

        # Create a mock document and CachedDocument
        mock_document = Document(
            page_content="Test content", metadata={"source": "http://test.com"}
        )
        mock_cached_document = CachedDocument(
            document=mock_document, timestamp=datetime.now(), ttl=timedelta(hours=1)
        )

        # Set up the cache with a mock entry
        web_loader._cache = {"http://test.com": mock_cached_document}

        # Call the method under test
        result = web_loader._get_cached_document("http://test.com")

        # Assert that the returned document matches the mock document
        assert result == mock_document

    def test_get_cached_document_valid(self):
        """
        Test _get_cached_document when a valid, non-expired document is in the cache.
        """
        webloader = WebLoader()
        url = "https://example.com"
        document = Document(page_content="Test content", metadata={"source": url})

        # Add a non-expired document to the cache
        current_time = datetime.now()
        webloader._cache[url] = CachedDocument(
            document=document, timestamp=current_time
        )

        result = webloader._get_cached_document(url)

        assert result == document
        assert len(webloader._cache) == 1

    def test_init_with_custom_values(self):
        """
        Test the initialization of WebLoader with custom values.
        """
        cache_ttl_hours = 48
        max_workers = 10
        loader = WebLoader(cache_ttl_hours=cache_ttl_hours, max_workers=max_workers)
        assert isinstance(loader._cache, dict)
        assert loader._cache == {}
        assert loader._cache_ttl == timedelta(hours=cache_ttl_hours)
        assert loader._max_workers == max_workers

    def test_init_with_default_values(self):
        """
        Test the initialization of WebLoader with default values.
        """
        loader = WebLoader()
        assert isinstance(loader._cache, dict)
        assert loader._cache == {}
        assert loader._cache_ttl == timedelta(hours=24)
        assert loader._max_workers == 5

    def test_init_with_extremely_large_cache_ttl(self):
        """
        Test initializing WebLoader with an extremely large cache TTL value.
        """
        with pytest.raises(ValueError):
            WebLoader(cache_ttl_hours=1000000000)

    def test_init_with_extremely_large_max_workers(self):
        """
        Test initializing WebLoader with an extremely large max_workers value.
        """
        with pytest.raises(ValueError):
            WebLoader(max_workers=1000000000)

    def test_init_with_float_cache_ttl(self):
        """
        Test initializing WebLoader with a float cache TTL value.
        """
        with pytest.raises(TypeError):
            WebLoader(cache_ttl_hours=24.5)

    def test_init_with_float_max_workers(self):
        """
        Test initializing WebLoader with a float max_workers value.
        """
        with pytest.raises(TypeError):
            WebLoader(max_workers=5.5)

    def test_init_with_negative_cache_ttl(self):
        """
        Test initializing WebLoader with a negative cache TTL value.
        """
        with pytest.raises(ValueError):
            WebLoader(cache_ttl_hours=-1)

    def test_init_with_negative_max_workers(self):
        """
        Test initializing WebLoader with a negative max_workers value.
        """
        with pytest.raises(ValueError):
            WebLoader(max_workers=-1)

    def test_init_with_non_integer_cache_ttl(self):
        """
        Test initializing WebLoader with a non-integer cache TTL value.
        """
        with pytest.raises(TypeError):
            WebLoader(cache_ttl_hours="24")

    def test_init_with_non_integer_max_workers(self):
        """
        Test initializing WebLoader with a non-integer max_workers value.
        """
        with pytest.raises(TypeError):
            WebLoader(max_workers="5")

    def test_init_with_zero_cache_ttl(self):
        """
        Test initializing WebLoader with a zero cache TTL value.
        """
        with pytest.raises(ValueError):
            WebLoader(cache_ttl_hours=0)

    def test_init_with_zero_max_workers(self):
        """
        Test initializing WebLoader with zero max_workers.
        """
        with pytest.raises(ValueError):
            WebLoader(max_workers=0)

    def test_is_expired_document_has_expired(self):
        """
        Test that is_expired returns True when the document has expired.
        """
        # Create a document that expired 1 hour ago
        doc = Document(page_content="Test content", metadata={})
        expired_time = datetime.now() - timedelta(hours=25)
        ttl = timedelta(hours=24)

        cached_doc = CachedDocument(document=doc, timestamp=expired_time, ttl=ttl)

        assert cached_doc.is_expired() == True

    def test_is_expired_document_not_expired(self):
        """
        Test that is_expired returns False when the document has not expired.
        """
        # Create a document that will expire in 1 hour
        doc = Document(page_content="Test content", metadata={})
        not_expired_time = datetime.now() - timedelta(hours=23)
        ttl = timedelta(hours=24)

        cached_doc = CachedDocument(document=doc, timestamp=not_expired_time, ttl=ttl)

        assert cached_doc.is_expired() == False

    def test_is_expired_with_future_timestamp(self):
        """
        Test is_expired method with a future timestamp.
        """
        doc = Document(page_content="Test content")
        future_time = datetime.now() + timedelta(days=1)
        cached_doc = CachedDocument(
            document=doc, timestamp=future_time, ttl=timedelta(hours=24)
        )
        assert cached_doc.is_expired() == False

    def test_is_expired_with_incorrect_ttl_type(self):
        """
        Test is_expired method with an incorrect TTL type.
        """
        doc = Document(page_content="Test content")
        with pytest.raises(TypeError):
            CachedDocument(document=doc, timestamp=datetime.now(), ttl="24 hours")

    def test_is_expired_with_invalid_timestamp(self):
        """
        Test is_expired method with an invalid timestamp.
        """
        doc = Document(page_content="Test content")
        with pytest.raises(TypeError):
            CachedDocument(
                document=doc, timestamp="invalid_timestamp", ttl=timedelta(hours=24)
            )

    def test_is_expired_with_negative_ttl(self):
        """
        Test is_expired method with a negative TTL.
        """
        doc = Document(page_content="Test content")
        cached_doc = CachedDocument(
            document=doc, timestamp=datetime.now(), ttl=timedelta(hours=-1)
        )
        assert cached_doc.is_expired() == True

    def test_is_expired_with_very_large_ttl(self):
        """
        Test is_expired method with a very large TTL.
        """
        doc = Document(page_content="Test content")
        cached_doc = CachedDocument(
            document=doc, timestamp=datetime.now(), ttl=timedelta(days=36500)
        )  # 100 years
        assert cached_doc.is_expired() == False

    def test_load_search_result_empty_input(self):
        """
        Test load_search_result with empty input
        """
        webloader = WebLoader()
        empty_results = RetrieverResults(results=[])
        documents, new_count, cached_count = webloader.load_search_result(empty_results)
        assert documents == []
        assert new_count == 0
        assert cached_count == 0

    def test_load_search_result_invalid_input_type(self):
        """
        Test load_search_result with invalid input type
        """
        webloader = WebLoader()
        with pytest.raises(AttributeError):
            webloader.load_search_result("invalid input")

    def test_load_search_result_invalid_result_format(self):
        """
        Test load_search_result with invalid result format
        """
        webloader = WebLoader()
        invalid_results = RetrieverResults(results=[{"url": "https://example.com"}])
        with pytest.raises(AttributeError):
            webloader.load_search_result(invalid_results)

    def test_load_search_result_mixed_cache_and_scrape(self):
        """
        Test load_search_result with a mix of cached and new documents requiring scraping
        """
        webloader = WebLoader()
        # Pre-cache a document
        cached_doc = Document(
            page_content="Cached content",
            metadata={"source": "https://cached.com", "title": "Cached"},
        )
        webloader._cache_document("https://cached.com", cached_doc)

        results = RetrieverResults(
            results=[
                RetrieverResult(
                    url="https://cached.com",
                    title="Cached",
                    content="",
                    require_scraping=False,
                ),
                RetrieverResult(
                    url="https://new.com",
                    title="New",
                    content="",
                    require_scraping=True,
                ),
            ]
        )

        with patch.object(WebLoader, "_batch_scrape_urls") as mock_scrape:
            mock_scrape.return_value = [
                Document(
                    page_content="New content",
                    metadata={"source": "https://new.com", "title": "New"},
                )
            ]
            documents, new_count, cached_count = webloader.load_search_result(results)

        assert len(documents) == 2
        assert new_count == 1
        assert cached_count == 1
        assert documents[0].page_content == "Cached content"
        assert documents[1].page_content == "New content"

    @patch("beano.researcher.webloader.WebLoader._batch_scrape_urls")
    def test_load_search_result_scraping_exception(self, mock_batch_scrape):
        """
        Test load_search_result when scraping throws an exception
        """
        mock_batch_scrape.side_effect = WebLoaderError("Scraping failed")
        webloader = WebLoader()
        results = RetrieverResults(
            results=[
                RetrieverResult(
                    url="https://example.com",
                    title="Example",
                    content="",
                    require_scraping=True,
                )
            ]
        )
        documents, new_count, cached_count = webloader.load_search_result(results)
        assert documents == []
        assert new_count == 1
        assert cached_count == 0

    def test_load_search_result_with_cache_and_scraping(self):
        """
        Test load_search_result with a mix of cached, non-scraped, and scraped results.
        """
        # Setup
        web_loader = WebLoader()

        # Mock search results
        mock_results = [
            RetrieverResult(
                url="http://cached.com",
                title="Cached",
                content="Cached content",
                require_scraping=False,
            ),
            RetrieverResult(
                url="http://no-scrape.com",
                title="No Scrape",
                content="No scrape content",
                require_scraping=False,
            ),
            RetrieverResult(
                url="http://scrape.com",
                title="Scrape",
                content="",
                require_scraping=True,
            ),
        ]
        search_results = RetrieverResults(results=mock_results)

        # Mock cached document
        cached_doc = Document(
            page_content="Cached content",
            metadata={"source": "http://cached.com", "title": "Cached"},
        )
        web_loader._get_cached_document = Mock(side_effect=[cached_doc, None, None])

        # Mock document creation
        web_loader._create_document = Mock(
            return_value=Document(
                page_content="No scrape content",
                metadata={"source": "http://no-scrape.com", "title": "No Scrape"},
            )
        )

        # Mock scraping
        scraped_doc = Document(
            page_content="Scraped content",
            metadata={"source": "http://scrape.com", "title": "Scrape"},
        )
        web_loader._batch_scrape_urls = Mock(return_value=[scraped_doc])

        # Mock caching
        web_loader._cache_document = Mock()

        # Execute
        documents, new_count, cached_count = web_loader.load_search_result(
            search_results
        )

        # Assert
        assert len(documents) == 3
        assert new_count == 2
        assert cached_count == 1

        # Verify method calls
        web_loader._get_cached_document.assert_any_call("http://cached.com")
        web_loader._get_cached_document.assert_any_call("http://no-scrape.com")
        web_loader._get_cached_document.assert_any_call("http://scrape.com")

        web_loader._create_document.assert_called_once_with(mock_results[1])
        web_loader._batch_scrape_urls.assert_called_once_with(["http://scrape.com"])

        web_loader._cache_document.assert_any_call("http://no-scrape.com", documents[1])
        web_loader._cache_document.assert_any_call("http://scrape.com", scraped_doc)

        # Verify document contents
        assert documents[0].page_content == "Cached content"
        assert documents[1].page_content == "No scrape content"
        assert documents[2].page_content == "Scraped content"

    def test_load_search_result_with_cached_and_new_documents(self):
        """
        Test load_search_result with a mix of cached and new documents,
        including one that requires scraping.
        """
        # Setup
        webloader = WebLoader()

        # Mock search results
        mock_results = [
            RetrieverResult(
                url="http://cached.com",
                title="Cached",
                content="Cached content",
                require_scraping=False,
            ),
            RetrieverResult(
                url="http://new.com",
                title="New",
                content="New content",
                require_scraping=False,
            ),
            RetrieverResult(
                url="http://scrape.com",
                title="Scrape",
                content="",
                require_scraping=True,
            ),
        ]
        search_results = RetrieverResults(results=mock_results)

        # Mock cached document
        cached_doc = Document(
            page_content="Cached content",
            metadata={"source": "http://cached.com", "title": "Cached"},
        )
        webloader._get_cached_document = Mock(side_effect=[cached_doc, None, None])

        # Mock document creation
        new_doc = Document(
            page_content="New content",
            metadata={"source": "http://new.com", "title": "New"},
        )
        webloader._create_document = Mock(return_value=new_doc)

        # Mock document caching
        webloader._cache_document = Mock()

        # Mock batch scraping
        scraped_doc = Document(
            page_content="Scraped content",
            metadata={"source": "http://scrape.com", "title": "Scrape"},
        )
        webloader._batch_scrape_urls = Mock(return_value=[scraped_doc])

        # Execute
        documents, new_count, cached_count = webloader.load_search_result(
            search_results
        )

        # Assert
        assert len(documents) == 3
        assert new_count == 2
        assert cached_count == 1

        assert documents[0] == cached_doc
        assert documents[1] == new_doc
        assert documents[2] == scraped_doc

        webloader._get_cached_document.assert_called_with("http://scrape.com")
        webloader._create_document.assert_called_once_with(mock_results[1])
        webloader._cache_document.assert_called_with("http://new.com", new_doc)
        webloader._batch_scrape_urls.assert_called_once_with(["http://scrape.com"])
        webloader._cache_document.assert_called_with("http://scrape.com", scraped_doc)

    def test_load_search_result_with_cached_and_new_documents_2(self):
        """
        Test load_search_result with a mix of cached and new documents, including one that requires scraping.
        """
        # Setup
        webloader = WebLoader()

        # Mock search results
        mock_results = [
            RetrieverResult(
                url="http://cached.com",
                title="Cached",
                content="Cached content",
                require_scraping=False,
            ),
            RetrieverResult(
                url="http://new.com",
                title="New",
                content="New content",
                require_scraping=False,
            ),
            RetrieverResult(
                url="http://scrape.com",
                title="Scrape",
                content="",
                require_scraping=True,
            ),
        ]
        search_results = RetrieverResults(results=mock_results)

        # Mock cached document
        cached_doc = Document(
            page_content="Cached content",
            metadata={"source": "http://cached.com", "title": "Cached"},
        )
        webloader._get_cached_document = MagicMock(side_effect=[cached_doc, None, None])

        # Mock document creation
        new_doc = Document(
            page_content="New content",
            metadata={"source": "http://new.com", "title": "New"},
        )
        webloader._create_document = MagicMock(return_value=new_doc)

        # Mock caching
        webloader._cache_document = MagicMock()

        # Execute
        documents, new_count, cached_count = webloader.load_search_result(
            search_results
        )

        # Assert
        assert len(documents) == 2
        assert new_count == 2
        assert cached_count == 1

        assert documents[0] == cached_doc
        assert documents[1] == new_doc

        webloader._cache_document.assert_called_once_with("http://new.com", new_doc)

        # Verify that _batch_scrape_urls was not called
        assert (
            not hasattr(webloader, "_batch_scrape_urls")
            or not webloader._batch_scrape_urls.called
        )

    def test_load_search_result_with_scraping_required(self):
        """
        Test load_search_result when cache is empty and scraping is required.
        """
        # Setup
        web_loader = WebLoader()
        mock_result = RetrieverResult(
            url="https://example.com",
            title="Example",
            content="",
            require_scraping=True,
        )
        search_results = RetrieverResults(results=[mock_result])

        # Mock _get_cached_document to return None (simulating empty cache)
        web_loader._get_cached_document = Mock(return_value=None)

        # Mock _batch_scrape_urls to return a sample scraped document
        scraped_doc = Document(
            page_content="Scraped content", metadata={"source": "https://example.com"}
        )
        web_loader._batch_scrape_urls = Mock(return_value=[scraped_doc])

        # Mock _cache_document to do nothing
        web_loader._cache_document = Mock()

        # Execute
        documents, new_count, cached_count = web_loader.load_search_result(
            search_results
        )

        # Assert
        assert len(documents) == 1
        assert documents[0].page_content == "Scraped content"
        assert new_count == 1
        assert cached_count == 0
        web_loader._batch_scrape_urls.assert_called_once_with(["https://example.com"])
        web_loader._cache_document.assert_called_once_with(
            "https://example.com", scraped_doc
        )

    def test_remove_expired_cache(self):
        """
        Test that remove_expired_cache removes only expired items from the cache.
        """
        # Initialize WebLoader
        web_loader = WebLoader(cache_ttl_hours=1)

        # Create test documents
        doc1 = Document(page_content="Content 1", metadata={"source": "url1"})
        doc2 = Document(page_content="Content 2", metadata={"source": "url2"})
        doc3 = Document(page_content="Content 3", metadata={"source": "url3"})

        # Add documents to cache with different timestamps
        web_loader._cache = {
            "url1": CachedDocument(
                doc1, datetime.now() - timedelta(hours=2)
            ),  # Expired
            "url2": CachedDocument(doc2, datetime.now()),  # Not expired
            "url3": CachedDocument(
                doc3, datetime.now() - timedelta(minutes=30)
            ),  # Not expired
        }

        # Call the method
        removed_count = web_loader.remove_expired_cache()

        # Assertions
        assert removed_count == 1  # One item should be removed
        assert len(web_loader._cache) == 2  # Two items should remain
        assert "url1" not in web_loader._cache  # Expired item should be removed
        assert "url2" in web_loader._cache  # Non-expired items should remain
        assert "url3" in web_loader._cache

    def test_remove_expired_cache_exception_handling(self):
        """
        Test remove_expired_cache exception handling when cache is corrupted.
        """
        webloader = WebLoader()
        webloader._cache = {"invalid_key": "invalid_value"}  # Corrupt the cache

        with pytest.raises(AttributeError):
            webloader.remove_expired_cache()

    def test_remove_expired_cache_with_all_expired_items(self):
        """
        Test remove_expired_cache when all items in the cache are expired.
        """
        webloader = WebLoader()
        doc = Document(page_content="Test", metadata={"source": "http://test.com"})
        webloader._cache = {
            "http://test.com": CachedDocument(
                document=doc,
                timestamp=datetime.now() - timedelta(hours=25),
                ttl=timedelta(hours=24),
            )
        }
        removed = webloader.remove_expired_cache()
        assert removed == 1, "Should return 1 when all items are expired"
        assert len(webloader._cache) == 0, "Cache should be empty after removal"

    def test_remove_expired_cache_with_empty_cache(self):
        """
        Test remove_expired_cache when the cache is empty.
        """
        webloader = WebLoader()
        removed = webloader.remove_expired_cache()
        assert removed == 0, "Should return 0 when cache is empty"

    def test_remove_expired_cache_with_mixed_expiration(self):
        """
        Test remove_expired_cache with a mix of expired and non-expired items.
        """
        webloader = WebLoader()
        doc1 = Document(page_content="Test1", metadata={"source": "http://test1.com"})
        doc2 = Document(page_content="Test2", metadata={"source": "http://test2.com"})
        webloader._cache = {
            "http://test1.com": CachedDocument(
                document=doc1,
                timestamp=datetime.now() - timedelta(hours=25),
                ttl=timedelta(hours=24),
            ),
            "http://test2.com": CachedDocument(
                document=doc2, timestamp=datetime.now(), ttl=timedelta(hours=24)
            ),
        }
        removed = webloader.remove_expired_cache()
        assert removed == 1, "Should return 1 when one item is expired"
        assert len(webloader._cache) == 1, "Cache should have one item after removal"
        assert (
            "http://test2.com" in webloader._cache
        ), "Non-expired item should remain in cache"

    def test_remove_expired_cache_with_modified_cache_ttl(self):
        """
        Test remove_expired_cache with a modified cache TTL.
        """
        webloader = WebLoader(cache_ttl_hours=1)  # Set TTL to 1 hour
        doc = Document(page_content="Test", metadata={"source": "http://test.com"})
        webloader._cache = {
            "http://test.com": CachedDocument(
                document=doc,
                timestamp=datetime.now() - timedelta(minutes=59),
                ttl=timedelta(hours=1),
            )
        }
        removed = webloader.remove_expired_cache()
        assert removed == 0, "Should return 0 when item is not yet expired"
        assert len(webloader._cache) == 1, "Cache should remain unchanged"

    def test_remove_expired_cache_with_no_expired_items(self):
        """
        Test remove_expired_cache when there are no expired items in the cache.
        """
        webloader = WebLoader()
        doc = Document(page_content="Test", metadata={"source": "http://test.com"})
        webloader._cache = {
            "http://test.com": CachedDocument(
                document=doc, timestamp=datetime.now(), ttl=timedelta(hours=24)
            )
        }
        removed = webloader.remove_expired_cache()
        assert removed == 0, "Should return 0 when no items are expired"
        assert len(webloader._cache) == 1, "Cache should remain unchanged"

    def test_scrape_single_url_empty_result(self):
        """
        Test that _scrape_single_url returns None when no documents are loaded.
        """
        url = "https://example.com"

        with patch("beano.researcher.webloader.WebBaseLoader") as MockWebBaseLoader:
            mock_loader = MagicMock()
            mock_loader.load.return_value = []
            MockWebBaseLoader.return_value = mock_loader

            web_loader = WebLoader()
            result = web_loader._scrape_single_url(url)

            assert result is None
            MockWebBaseLoader.assert_called_once_with([url])
            mock_loader.load.assert_called_once()

    def test_scrape_single_url_exception(self):
        """
        Test that _scrape_single_url raises a WebLoaderError when an exception occurs.
        """
        url = "https://example.com"

        with patch("beano.researcher.webloader.WebBaseLoader") as MockWebBaseLoader:
            mock_loader = MagicMock()
            mock_loader.load.side_effect = Exception("Test error")
            MockWebBaseLoader.return_value = mock_loader

            web_loader = WebLoader()

            with pytest.raises(WebLoaderError) as exc_info:
                web_loader._scrape_single_url(url)

            assert str(exc_info.value) == f"Failed to scrape {url}: Test error"
            MockWebBaseLoader.assert_called_once_with([url])
            mock_loader.load.assert_called_once()

    def test_scrape_single_url_success(self):
        """
        Test that _scrape_single_url successfully scrapes a URL and returns a Document.
        """
        url = "https://example.com"
        mock_doc = Document(page_content="Test content", metadata={"source": url})

        with patch("beano.researcher.webloader.WebBaseLoader") as MockWebBaseLoader:
            mock_loader = MagicMock()
            mock_loader.load.return_value = [mock_doc]
            MockWebBaseLoader.return_value = mock_loader

            web_loader = WebLoader()
            result = web_loader._scrape_single_url(url)

            assert isinstance(result, Document)
            assert result.page_content == "Test content"
            assert result.metadata["source"] == url
            MockWebBaseLoader.assert_called_once_with([url])
            mock_loader.load.assert_called_once()
