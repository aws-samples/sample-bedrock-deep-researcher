
import logging
import os
from typing import List, Optional

from pydantic import BaseModel

from beano.researcher import Researcher, ResearcherConfig
from beano.researcher.retrievers.retrievers import RetrieverType

from .model import Section
from .utils import exponential_backoff_retry

logger = logging.getLogger(__name__)


class Queries(BaseModel):
    queries: List[str]


class ResearchContent(BaseModel):
    content: str
    references: List[str]


class ResearchAgent:

    def __init__(self, model, retriever: RetrieverType = RetrieverType.GOOGLE):
        self.model = model
        self.config = ResearcherConfig(
            llm_model_id=model,
            retrievers=[retriever],
            retrievers_config={
                "tavily_access_key": os.environ["TAVILY_API_KEY"]
            }
        )
        self.input_tokens = 0
        self.output_tokens = 0
        self.execution_time_in_seconds = 0
        self.researcher = Researcher(config=self.config)

    @exponential_backoff_retry(Exception)
    def _invoke_model(self, messages) -> Optional[Queries]:
        """Invoke the model with retry logic for ServiceUnavailableError."""
        return self.model.with_structured_output(Queries).invoke(messages)

    def run_initial_search(self, state: dict) -> dict:
        """
        Perform initial research on the task topic.

        Args:
            state (dict): Contains task information

        Returns:
            dict: Initial research results
        """
        task = state['task']
        initial_research_input_tokens = state.get(
            "initial_research_input_tokens", 0)
        initial_research_output_tokens = state.get(
            "initial_research_output_tokens", 0)

        initial_research_execution_time = state.get(
            "initial_research_execution_time", 0)

        logger.info("Performing initial research on the task topic")

        try:
            results = self.researcher.simple_research(
                task['topic'], max_results=2)

            documents = results.documents
            initial_research_input_tokens += results.metadata.input_tokens
            initial_research_output_tokens += results.metadata.output_tokens
            initial_research_execution_time += results.metadata.execution_time_in_seconds

            logger.debug(f"Initial search results: {documents}")

            return {"initial_research": documents,
                    "initial_research_input_tokens": initial_research_input_tokens,
                    "initial_research_output_tokens": initial_research_output_tokens,
                    "initial_research_execution_time": initial_research_execution_time}

        except Exception as e:
            logger.error(f"Error during initial search: {str(e)}")
            return {"initial_research": []}

    def run_subquery_research(self, state: dict) -> dict:
        """
        Performs research by generating and executing queries for each section.

        Args:
            state (dict): Contains sections and configuration parameters

        Returns:
            dict: Updated state with research results
        """
        logger.info("Starting section-based research")
        sections = state.get("sections", [])
        task = state['task']

        num_queries = state.get("number_of_queries", 2)

        try:
            return {
                "sections": [
                    self._process_section(
                        task.get('topic'), section, num_queries)
                    for section in sections
                ]
            }
        except Exception as e:
            logger.error(f"Error during subquery research: {str(e)}")
            return {"sections": sections}

    def _process_section(self, topic: str, section: Section, num_queries: int) -> dict:
        """
        Process a single section by generating and executing queries.

        Args:
            section (dict): Section information including title
            num_queries (int): Number of queries to generate

        Returns:
            dict: Section with added research data
        """
        try:
            section_title = section.title
            logger.info(f"Generating {num_queries} queries for section {
                        section_title}")
            results = self.researcher.deep_research(
                section_title, context=topic, max_results=2, num_queries=num_queries)

            logger.info(f"Deep Search Results {len(results.documents)}")
            self.input_tokens += results.metadata.input_tokens
            self.output_tokens += results.metadata.output_tokens
            self.execution_time_in_seconds = results.metadata.execution_time_in_seconds

            section.documents = results.documents
            return section
        except Exception as e:
            logger.error(f"Error processing section {
                         section.title}: {str(e)}")
            section['research_data'] = []
            return section
