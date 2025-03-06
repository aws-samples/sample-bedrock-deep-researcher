import logging
from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.constants import Send
from langgraph.types import Command, interrupt

from bedrock_deep_research.config import Configuration

from ..model import ArticleState
from .article_outline_generator import ArticleOutlineGenerator

logger = logging.getLogger(__name__)


class HumanFeedbackProvider:
    N = "human_feedback"

    def __call__(
        self, state: ArticleState, config: RunnableConfig
    ) -> Command[Literal[ArticleOutlineGenerator.N, "build_section_with_web_research"]]:
        """Get feedback on the article outline"""

        # Get sections
        sections = state["sections"]
        outline = state["messages"][-1]

        # Get configuration
        configurable = Configuration.from_runnable_config(config)

        feedback = interrupt(
            f"Please provide feedback on the following article outline. \n\n{outline.content}\n\n Are the article outline and title meeting your needs? Pass 'ok' to approve it or provide feedback to regenerate it:"
        )

        if feedback == "ok":
            # Treat this as approve and kick off section writing
            return Command(
                goto=[
                    Send(
                        "build_section_with_web_research",
                        {"section": s, "search_iterations": 0},
                    )
                    for s in sections
                    if s.research
                ]
            )

        # If the user provides feedback, regenerate the report plan
        else:

            feedback = f"<user feedback>{feedback}</user feedback> <Original Outline>{outline.content}</Original Outline>"
            # treat this as feedback
            return Command(
                goto=ArticleOutlineGenerator.N,
                update={"feedback_on_report_plan": feedback},
            )
