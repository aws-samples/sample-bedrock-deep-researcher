import asyncio
import logging
from typing import List

from botocore.exceptions import ClientError
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from ..config import Configuration
from ..model import ArticleInputState, Queries
from ..utils import exponential_backoff_retry, format_web_search
from ..web_search import WebSearch

logger = logging.getLogger(__name__)

system_prompt_template = """You are an expert technical writer, helping to structure an article content on the topic: "{topic}"

<instructions>
{article_organization}
</instructions>

Your task is to generate {number_of_queries} search queries that will help gather comprehensive information for planning the article sections.

The queries should:
1. Be relevant to the topic
2. Help satisfy the requirements specified in instructions.

Make the queries detailed but specific enough to find high-quality, relevant sources while covering the breadth needed for the article structure."""


class InitialResearcher:
    N = "initial_research"

    def __init__(self, web_search: WebSearch):
        self.web_search = web_search

    def __call__(self, state: ArticleInputState, config: RunnableConfig):
        logging.info("initial_research")

        topic = state["topic"]
        configurable = Configuration.from_runnable_config(config)

        system_prompt = system_prompt_template.format(
            topic=topic,
            article_organization=configurable.report_structure,
            number_of_queries=configurable.number_of_queries,
        )

        user_prompt = "Generate search queries on the provided topic."

        query_list = self.generate_search_queries(
            configurable.planner_model, configurable.max_tokens, system_prompt, user_prompt)

        logger.info(f"Generated queries: {query_list}")

        search_results = asyncio.run(self.web_search.search(query_list))

        source_str = format_web_search(
            search_results, max_tokens_per_source=1000, include_raw_content=False
        )

        return {"source_str": source_str}

    @exponential_backoff_retry(ClientError, max_retries=10)
    def generate_search_queries(self, model_id: str, max_tokens: int, system_prompt: str, user_prompt: str) -> List[str]:
        planner_model = ChatBedrock(
            model_id=model_id, max_tokens=max_tokens)

        structured_model = planner_model.with_structured_output(Queries)

        # Generate queries
        results = structured_model.invoke(
            [SystemMessage(content=system_prompt)]
            + [
                HumanMessage(
                    content=user_prompt
                )
            ]
        )

        return results.queries
