import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor

import boto3
from langchain_aws import BedrockEmbeddings, ChatBedrock

from beano.researcher.webloader import WebLoader

from .models import (DeepSearchQueries, ResearcherConfig, ResearchMetadata,
                     ResearchResults)
from .prompts import generate_search_queries_prompt
from .retrievers import (RetrieverResults, RetrieverType,
                         retriever_service_provider)

logger = logging.getLogger(__name__)


class Researcher:
    def __init__(self, config: ResearcherConfig):
        self.config = config
        self.webloader = WebLoader()
        self.retrievers = []
        # self.scraped_urls: dict[str, Document] = {}

        if len(config.retrievers) > 0:
            for retriever in config.retrievers:
                self.retrievers.append(retriever_service_provider.get(
                    RetrieverType(retriever), **config.retrievers_config))
        else:
            # Default retriever
            self.retrievers = [retriever_service_provider.get(
                RetrieverType.TAVILY, **config.retrievers_config)]

        # self.bedrock_client = boto3.client(service_name='bedrock-runtime',
        #                                    region_name=self.config.aws_region)

        # self.embeddings = BedrockEmbeddings(model_id=self.config.embedding_model_id,
        #                                     client=self.bedrock_client)

    def _aggregate_research_results(self, query: str, docs: list,
                                    scraped_docs: int, cached_docs: int, start_time: float,
                                    sub_queries: list = None) -> ResearchResults:
        execution_time = time.time() - start_time
        logger.debug(f"Research execution time: {execution_time:.2f} seconds")

        metadata = ResearchMetadata(execution_time_in_seconds=execution_time,
                                    scraped_documents=scraped_docs, cached_documents=cached_docs)

        return ResearchResults(
            query=query,
            sub_queries=sub_queries,
            documents=docs,
            metadata=metadata
        )

    def _execute_retriever_search(self, retriever, query: str, max_results: int) -> list:
        try:
            return retriever.search(query, max_results=max_results)
        except Exception as e:
            logger.error(f"Error during executing retriever {
                         retriever.service_id}: {str(e)}")
            return []

    def simple_research(self, query: str, max_results: int = 5) -> ResearchResults:
        start_time = time.time()

        all_results = []
        for retriever in self.retrievers:
            results = self._execute_retriever_search(
                retriever, query, max_results)

            logger.info(f"Retriever {retriever.service_id} results: {results}")
            all_results.extend(results)

        docs, scraped_docs, cached_docs = self.webloader.load_search_result(
            RetrieverResults(query=query, results=all_results))

        return self._aggregate_research_results(query, docs, scraped_docs, cached_docs, start_time)

    def deep_research(self, query: str, context: str = None, max_results: int = 5, num_queries: int = 5) -> ResearchResults:
        start_time = time.time()

        prompt = generate_search_queries_prompt(
            query=query, context=context, num_queries=num_queries)

        model = ChatBedrock(model_id=self.config.llm_model_id, streaming=True,
                            temperature=0.2).with_structured_output(DeepSearchQueries, include_raw=True)

        response = model.invoke(prompt)

        # logger.info(f"LLM response: {response}")
        queries = response['parsed']
        usage_metadata = response['raw'].usage_metadata

        logger.info(f"Generated queries: {queries}")

        docs = []
        cached_documents = 0
        scraped_documents = 0
        for sub_query in queries.queries:
            sub_query_research = self.simple_research(sub_query, max_results)

            docs.extend(sub_query_research.documents)
            scraped_documents += sub_query_research.metadata.scraped_documents
            cached_documents += sub_query_research.metadata.cached_documents

        execution_time = time.time() - start_time
        logger.debug(f"Deep research execution time: {
                     execution_time:.2f} seconds")

        metadata = ResearchMetadata(
            input_tokens=usage_metadata['input_tokens'],
            output_tokens=usage_metadata['output_tokens'],
            execution_time_in_seconds=execution_time,
            scraped_documents=scraped_documents, cached_documents=cached_documents
        )

        research_results = ResearchResults(
            query=query, sub_queries=queries.queries, documents=docs, metadata=metadata)
        return research_results

    async def deep_aresearch(self, query: str, context: str = None, max_results: int = 5, num_queries: int = 5) -> ResearchResults:
        start_time = time.time()

        # Generate queries (same as before)
        prompt = generate_search_queries_prompt(
            query=query, context=context, num_queries=num_queries)
        model = ChatBedrock(model_id=self.config.llm_model_id, streaming=True,
                            temperature=0.2).with_structured_output(DeepSearchQueries, include_raw=True)
        response = model.invoke(prompt)
        queries = response['parsed']
        usage_metadata = response['raw'].usage_metadata

        # Parallel processing of sub-queries
        docs = []
        cached_documents = 0
        scraped_documents = 0

        # async def process_query(sub_query):
        #     result = self.simple_research(sub_query, max_results)
        #     return result

        # Create tasks for all sub-queries
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            tasks = [loop.run_in_executor(executor, self.simple_research, sub_query, max_results)
                     for sub_query in queries.queries]
            results = await asyncio.gather(*tasks)

        # Aggregate results
        for result in results:
            docs.extend(result.documents)
            scraped_documents += result.metadata.scraped_documents
            cached_documents += result.metadata.cached_documents

        execution_time = time.time() - start_time

        metadata = ResearchMetadata(
            input_tokens=usage_metadata['input_tokens'],
            output_tokens=usage_metadata['output_tokens'],
            execution_time_in_seconds=execution_time,
            scraped_documents=scraped_documents,
            cached_documents=cached_documents
        )

        return ResearchResults(
            query=query,
            sub_queries=queries.queries,
            documents=docs,
            metadata=metadata
        )
