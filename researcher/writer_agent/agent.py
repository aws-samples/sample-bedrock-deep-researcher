import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from langchain_aws import ChatBedrock
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.outputs.llm_result import LLMResult
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .model import ResearchState
from .planner_node import PlannerNode
from .research_node import ResearchNode
from .writer_node import WriterNode

logger = logging.getLogger(__name__)


def human_plan_feedback(state: ResearchState):
    logger.info("Human feedback required")
    pass


@dataclass
class WorkflowConfig:
    """Configuration for workflow execution"""
    thread_id: str
    callables: List[BaseCallbackHandler]

    def to_dict(self) -> dict:
        return {"configurable": {"thread_id": self.thread_id}, "callbacks": self.callables}


class TokenCounterHandler(BaseCallbackHandler):

    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0

    def on_llm_end(self, response: LLMResult,  run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        logger.debug(f"Token Counter Handler: {response}")
        for g in response.generations:
            if isinstance(g, list):
                g = g[0]

            logger.info(
                f"Input Tokens: {g.message.usage_metadata['input_tokens']}")
            logger.info(f"Output Tokens: {
                        g.message.usage_metadata['output_tokens']}")
            self.input_tokens += g.message.usage_metadata["input_tokens"]
            self.output_tokens += g.message.usage_metadata["output_tokens"]


class WriterAgent:

    def __init__(self, model_id):
        self.model_id = model_id
        self.model = ChatBedrock(
            model_id=model_id, streaming=True, temperature=0)
        self.token_counter = TokenCounterHandler()
        self.agents = self._init_agents()

        self.workflow = self._create_workflow()
        checkpointer = MemorySaver()

        self.graph = self.workflow.compile(
            checkpointer=checkpointer, interrupt_before=["human_plan_feedback"])

    def _init_agents(self) -> Dict[str, Any]:
        return {
            "research_agent": ResearchNode(llm_model_id="amazon.nova-lite-v1:0", tavily_access_key=os.environ["TAVILY_API_KEY"]),
            "planner": PlannerNode(self.model),
            "writer": WriterNode(self.model),
        }

    def _create_workflow(self):
        workflow = StateGraph(ResearchState)
        workflow.add_node(
            "plan_research", self.agents["research_agent"].run_initial_search)
        workflow.add_node("planner", self.agents["planner"].run)
        workflow.add_node("human_plan_feedback", human_plan_feedback)
        workflow.add_node(
            "deep_research", self.agents["research_agent"].run_subquery_research)
        workflow.add_node("writer", self.agents["writer"].run)

        workflow.set_entry_point("plan_research")
        workflow.add_edge("plan_research", "planner")
        workflow.add_edge("planner", "human_plan_feedback")

        workflow.add_conditional_edges(
            'human_plan_feedback',
            self.accept_or_review_plan,
            {"accept": "deep_research", "revise": "planner"}
        )

        workflow.add_edge("deep_research", "writer")
        # workflow.add_edge("writer", "publisher")
        workflow.add_edge("writer", END)

        return workflow

    def accept_or_review_plan(self, review: ResearchState):
        """
        Determines if the plan should be accepted based on human feedback.

        Args:
            review (dict): Dictionary containing human_feedback

        Returns:
            str: 'accept' if feedback is empty or negative, 'revise' otherwise
        """
        feedback = review.get('human_feedback')
        valid_rejection_responses = {'', 'no', 'stop', 'ok', None}
        return "accept" if feedback in valid_rejection_responses else "revise"

    def run(self, task, task_id: str, callables: List[BaseCallbackHandler] = []) -> dict:
        """
        Execute the workflow for a given task.

        Args:
            task: The task to process
            task_id (str): Unique identifier for the task

        Returns:
            dict: Result of the workflow execution
        """
        callables.append(self.token_counter)

        config = WorkflowConfig(
            task_id, callables).to_dict()
        return self.graph.invoke({"task": task.dict()}, config=config)

    def provide_human_plan_feedback(self, task_id: str, human_feedback: str, callables: List[BaseCallbackHandler] = []) -> dict:
        """
        Update the workflow with human feedback.

        Args:
            task_id (str): Unique identifier for the task
            human_feedback (str): Feedback provided by human reviewer

        Returns:
            dict: Updated workflow state
        """
        callables.append(self.token_counter)

        config = WorkflowConfig(
            task_id, callables).to_dict()
        self.graph.update_state(
            config,
            {"human_feedback": human_feedback},
            as_node="human_plan_feedback"
        )
        return self.graph.invoke(None, config=config)

    def get_state(self, task_id: str, callables: List[BaseCallbackHandler] = []) -> dict:
        """
        Retrieve the current state of a workflow.

        Args:
            task_id (str): Unique identifier for the task

        Returns:
            dict: Current state of the workflow
        """

        config = WorkflowConfig(
            task_id, callables).to_dict()
        return self.graph.get_state(config)

    def input_tokens(self) -> int:
        """
        Retrieve the input tokens used by the model.

        Returns:
            int: Input tokens used by the model
        """
        return self.token_counter.input_tokens

    def output_tokens(self) -> int:
        """
        Retrieve the output tokens used by the model.

        Returns:
            int: Output tokens used by the model
        """
        return self.token_counter.output_tokens
