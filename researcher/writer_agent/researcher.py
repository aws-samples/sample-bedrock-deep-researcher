import logging
import time
from typing import List

from langchain_aws import ChatBedrockConverse
from langchain_core.documents import Document
from pydantic import BaseModel
from tavily import TavilyClient

from .model import ResearchMetadata, ResearchResults

logger = logging.getLogger(__name__)


class DeepSearchQueries(BaseModel):
    '''An answer to the user question to generate a number of google search queries'''
    queries: List[str]


def generate_search_queries_prompt_nova(
    query: str, context: str = None, num_queries: int = 3
):
    prompt_context = f"{context}" if context else ""

    return f"""
You are a seasoned research assistant tasked with generating a list of Google search queries to find relevant information for a given task. Follow these steps:

1. Review the task description:
<task>{query}</task>

2. Consider the provided context that may inform and refine your search queries:
<context>{prompt_context}</context>
This context provides real-time web information that can help you generate more specific and relevant queries. Take into account any current events, recent developments, or specific details mentioned in the context that could enhance the search queries.

3. Generate {num_queries} Google search queries that can help form an objective opinion on the given task, following these requirements:
- The response should contain ONLY the list of search queries, without any additional text.
- You MUST answer in JSON format only. Please follow the output schema below.

Output Schema:
[{{
        "queries": "list of queries goes here",
}}]
    """


class Researcher:
    def __init__(self, llm_model_id: str, tavily_access_key: str):
        self.llm_model_id = llm_model_id
        self.tavily = TavilyClient(api_key=tavily_access_key)

    def _aggregate_research_results(self, query: str, docs: List[Document], start_time: float,
                                    sub_queries: list = None) -> ResearchResults:
        execution_time = time.time() - start_time
        logger.debug(f"Research execution time: {execution_time:.2f} seconds")

        metadata = ResearchMetadata(execution_time_in_seconds=execution_time)

        return ResearchResults(
            query=query,
            sub_queries=sub_queries,
            documents=docs,
            metadata=metadata
        )

    def _search(self, query: str, max_results: int) -> List[Document]:
        research_results = []

        try:
            response = self.tavily.search(query, max_results=max_results)

            logger.info(f"Search results: {response}")
            for result in response["results"]:
                research_results.append(
                    Document(
                        page_content=result["content"],
                        metadata={
                            "source": result["url"], "title": result["title"]},
                    )
                )
        except Exception as e:
            logger.error(
                f"Error during executing retriever Tavily Search: {str(e)}")

        return research_results

    def simple_research(self, query: str, max_results: int = 5) -> ResearchResults:
        start_time = time.time()

        docs = self._search(query, max_results)

        # logger.info(f"Search results: {docs}")

        return self._aggregate_research_results(query, docs, start_time)

    def deep_research(self, query: str, context: str = None, max_results: int = 5, num_queries: int = 5) -> ResearchResults:
        start_time = time.time()

        prompt = generate_search_queries_prompt_nova(
            query=query, context=context, num_queries=num_queries)

        model = ChatBedrockConverse(model_id=self.llm_model_id,
                                    temperature=0.2).with_structured_output(DeepSearchQueries, include_raw=True)

        response = model.invoke(prompt)

        logger.debug(f"LLM response: {response}")
        queries = response['parsed']
        usage_metadata = response['raw'].usage_metadata

        logger.info(f"Generated queries: {queries}")

        docs = []

        for sub_query in queries.queries:
            sub_query_research = self.simple_research(sub_query, max_results)

            docs.extend(sub_query_research.documents)

        execution_time = time.time() - start_time
        logger.debug(f"Deep research execution time: {
                     execution_time:.2f} seconds")

        metadata = ResearchMetadata(
            input_tokens=usage_metadata['input_tokens'],
            output_tokens=usage_metadata['output_tokens'],
            execution_time_in_seconds=execution_time
        )

        research_results = ResearchResults(
            query=query, sub_queries=queries.queries, documents=docs, metadata=metadata)
        return research_results
