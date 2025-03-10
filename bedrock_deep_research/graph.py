import logging

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command, interrupt

from .config import Configuration
from .model import (ArticleInputState, ArticleOutputState, ArticleState,
                    SectionOutputState, SectionState)
from .nodes import (ArticleHeadImageGenerator, ArticleOutlineGenerator,
                    CompileFinalArticle, CompletedSectionsFormatter,
                    FinalSectionsWriter, HumanFeedbackProvider,
                    InitialResearcher, SectionSearchQueryGenerator,
                    SectionWebResearcher, SectionWriter,
                    initiate_final_section_writing)
from .tools import web_search_and_rewrite_article
from .web_search import WebSearch

logger = logging.getLogger(__name__)


def wait_for_feedback(state: ArticleState):
    human_message = interrupt("Please provide feedback:")
    return {
        "messages": [
            {
                "role": "human",
                "content": human_message
            }
        ]
    }


class BedrockDeepResearch:
    def __init__(self, config: dict, tavily_api_key: str):
        self.config = config
        self.web_search = WebSearch(tavily_api_key, save_search_results=False)
        self.graph = self.__create_workflow()

    def __create_workflow(self):

        # Subgraph to research and write each section
        def _section_subgraph():
            # Subgraph: Add nodes
            section_builder = StateGraph(
                SectionState, output=SectionOutputState)
            section_builder.add_node(
                SectionSearchQueryGenerator.N, SectionSearchQueryGenerator()
            )
            section_builder.add_node(
                SectionWebResearcher.N, SectionWebResearcher(self.web_search)
            )
            section_builder.add_node(SectionWriter.N, SectionWriter())

            # Subgraph: Add edges
            section_builder.add_edge(START, SectionSearchQueryGenerator.N)
            section_builder.add_edge(
                SectionSearchQueryGenerator.N, SectionWebResearcher.N)
            section_builder.add_edge(SectionWebResearcher.N, SectionWriter.N)
            return section_builder.compile()

        react_agent_model = ChatBedrock(
            model="us.anthropic.claude-3-5-haiku-20241022-v1:0", temperature=0)

        react_agent_tools = [web_search_and_rewrite_article]

        # Build the main graph
        builder = StateGraph(
            ArticleState,
            input=ArticleInputState,
            output=ArticleOutputState,
            config_schema=Configuration,
        )
        builder.add_node(InitialResearcher.N,
                         InitialResearcher(self.web_search))
        builder.add_node(ArticleOutlineGenerator.N, ArticleOutlineGenerator())
        builder.add_node(HumanFeedbackProvider.N, HumanFeedbackProvider())
        builder.add_node("build_section_with_web_research",
                         _section_subgraph())
        builder.add_node(CompletedSectionsFormatter.N,
                         CompletedSectionsFormatter())
        builder.add_node(FinalSectionsWriter.N, FinalSectionsWriter())
        builder.add_node(ArticleHeadImageGenerator.N,
                         ArticleHeadImageGenerator())
        builder.add_node(CompileFinalArticle.N, CompileFinalArticle())
        builder.add_node("wait_for_feedback", wait_for_feedback)
        builder.add_node("react_agent", create_react_agent(
            model=react_agent_model, tools=react_agent_tools, prompt="You are an expert article editor. Your task is to apply user feedback to the draft of the article using the available tools"))

        # Add edges
        builder.add_edge(START, InitialResearcher.N)
        builder.add_edge(InitialResearcher.N, ArticleOutlineGenerator.N)
        builder.add_edge(ArticleOutlineGenerator.N, HumanFeedbackProvider.N)
        builder.add_edge(
            "build_section_with_web_research", CompletedSectionsFormatter.N
        )
        builder.add_conditional_edges(
            CompletedSectionsFormatter.N,
            initiate_final_section_writing,
            [FinalSectionsWriter.N],
        )
        builder.add_edge(CompletedSectionsFormatter.N,
                         ArticleHeadImageGenerator.N)
        builder.add_edge(ArticleHeadImageGenerator.N,
                         CompileFinalArticle.N)

        builder.add_edge(FinalSectionsWriter.N, CompileFinalArticle.N)
        # builder.add_edge(ArticleHeadImageGenerator.N, CompileFinalArticle.N)
        builder.add_edge(CompileFinalArticle.N, "wait_for_feedback")
        builder.add_edge("wait_for_feedback", "react_agent")

        memory = MemorySaver()

        return builder.compile(checkpointer=memory)

    def start(self, topic: str):
        """Starts the workflow with the given topic."""

        logger.debug(f"Starting workflow with topic: {topic}")

        return self.graph.invoke(
            {"topic": topic}, self.config
        )

    def feedback(self, feedback):
        """Provides feedback to the workflow."""

        logger.info(f"Feedback received: {feedback}")

        return self.graph.invoke(
            Command(resume=feedback, update={
                    "messages": HumanMessage(content=feedback)}), self.config
        )

    def stream(self, message):
        """Provides feedback to the workflow."""

        logger.info(f"Message received: {message}")

        return self.graph.stream(
            Command(resume=message), self.config, stream_mode="messages"
        )

    def get_state(self):
        """Returns the current state of the workflow."""

        return self.graph.get_state(self.config)
