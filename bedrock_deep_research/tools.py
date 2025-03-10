import asyncio
import logging
import os

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_core.tools.base import InjectedToolCallId
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from typing_extensions import Annotated

from .config import Configuration
from .utils import exponential_backoff_retry, format_web_search
from .web_search import WebSearch

logger = logging.getLogger(__name__)


@exponential_backoff_retry(Exception, max_retries=10)
def invoke_llm(model_id: str, max_tokens: int, system_prompt: str, user_prompt: str):

    planner_model = ChatBedrock(
        model_id=model_id, max_tokens=max_tokens
    )

    return planner_model.invoke(
        [SystemMessage(content=system_prompt)]
        + [
            HumanMessage(
                content=user_prompt
            )
        ]
    )


@tool
def web_search_and_rewrite_article(query: str, tool_call_id: Annotated[str, InjectedToolCallId], config: RunnableConfig, state: Annotated[dict, InjectedState]) -> str:
    """Search the web for information on the topic and rewrite the article based on the search results."""

    configurable = Configuration.from_runnable_config(config)

    logger.info(f"web_search_and_rewrite_article: {query}")
    final_report = state['final_report']

    web_search = WebSearch(tavily_api_key=os.getenv("TAVILY_API_KEY"))

    search_results = asyncio.run(web_search.search(query))

    search_results_str = format_web_search(
        search_results, max_tokens_per_source=5000, include_raw_content=False
    )
    system_prompt = """You are an expert technical writer tasked to update the existing article draft with the web search results.
- The current draft of the article is provided in <article_draft>
- You must update the <article_draft> to include the informations provided in <web_search_results>
- Use the writing guidelines provided in <writing_guidelines> to apply writing style and writing instructions
- You must NEVER change organization of the article, like adding or removing sections
- You must NEVER change the title nor the section titles
- Return only the article text in Markdown format and nothing else
"""

    user_prompt = f"""<article_draft>
{final_report}
</article_draft>

<web_search_results>
{search_results_str}
</web_search_results>

<writing_guidelines>
{configurable.writing_guidelines}
</writing_guidelines>
"""

    article_draft = invoke_llm(
        model_id=configurable.writer_model,
        max_tokens=configurable.max_tokens,
        system_prompt=system_prompt,
        user_prompt=user_prompt
    ).content

    return Command(
        update={
            # update the state keys
            "final_report": article_draft,
            # update the message history
            "messages": [
                ToolMessage(
                    article_draft, tool_call_id=tool_call_id
                )
            ],
        }
    )
