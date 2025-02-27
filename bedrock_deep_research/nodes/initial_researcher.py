import logging
import uuid

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from ..config import Configuration
from ..model import ArticleInputState, Queries
from ..utils import format_web_search
from ..web_search import WebSearch

logger = logging.getLogger(__name__)

article_planner_query_writer_instructions = """You are an expert technical writer, helping to structure an article content on the topic: "{topic}"

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

    async def __call__(self, state: ArticleInputState, config: RunnableConfig):
        logging.info("Generating report plan")

        configurable = Configuration.from_runnable_config(config)

        planner_model = ChatBedrock(model_id=configurable.planner_model)

        structured_model = planner_model.with_structured_output(Queries)
        # Format system instructions
        system_instructions_query = article_planner_query_writer_instructions.format(
            topic=state["topic"],
            article_organization=configurable.report_structure,
            number_of_queries=configurable.number_of_queries,
        )

        # Generate queries
        results = structured_model.invoke(
            [SystemMessage(content=system_instructions_query)]
            + [
                HumanMessage(
                    content="Generate search queries that will help with planning the sections of the article."
                )
            ]
        )

        logger.info(f"Generated queries: {results.queries}")

        # Web search
        query_list = results.queries

        search_results = await self.web_search.search(query_list)

        source_str = format_web_search(
            search_results, max_tokens_per_source=1000, include_raw_content=False
        )

        return {"article_id": str(uuid.uuid4()), "source_str": source_str}
