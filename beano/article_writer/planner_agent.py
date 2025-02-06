import logging
from datetime import datetime
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from .model import Section
from .utils import exponential_backoff_retry

logger = logging.getLogger(__name__)


class Outline(BaseModel):
    title: str
    sections: List[Section]
    date: str


class PlannerAgent:

    SYSTEM_PROMPT = (
        "You are a research editor. Your goal is to oversee the research project "
        "from inception to completion. Your main task is to plan the article outline "
        "based on an initial research summary."
    )

    USER_PROMPT = """
        Task: Generate an outline of sections headers for the research project on the topic enclosed in the <topic> tag.
        To generate the article outline use the initial research context enclosed in the <initial_research> tag and the user requirements enclosed in the <requirements> tag.
        Today's date is {today}.

        Instructions:
        1. You must generate a maximum of {max_sections} section headers.
        2. Avoid including the title of the article or any section headings
        3. Avoid using acronyms in the section headers.
        4. You must return nothing but a JSON with the fields 'title' (str) and sections' (maximum {max_sections} section headers) with the following structure:
        '{{title: string research title, date: today's date, sections: [ {{'title: 'section header 1'}}, {{ 'title': 'section header 2' }}, {{ 'title': 'section header 3' }} ...]}}'.
        {feedback_instruction}

        Topic:
        <topic>
        {topic}
        </topic>

        Initial research context:
        <initial_research>
        {initial_research}
        </initial_research>

        User Requirements:
        <requirements>
        {requirements}
        </requirements>
        """

    def __init__(self, model):
        self.model = model

    @exponential_backoff_retry(Exception)
    def _invoke_model(self, messages) -> Optional[Outline]:
        """Invoke the model with retry logic for ServiceUnavailableError."""
        return self.model.with_structured_output(Outline).invoke(messages)

    def run(self, state: dict):
        logger.info(f"PlannerAgent.run")

        task = state.get('task')
        topic = task.get('topic')
        requirements = task.get('requirements')
        max_sections = task.get('max_sections')
        initial_research = state.get('initial_research')
        today = datetime.now().strftime('%d/%m/%Y')
        human_feedback = state.get("human_feedback")

        docs_content = "\n\n".join(
            doc.page_content for doc in initial_research)

        feedback_instruction = (
            f"Human feedback: {
                human_feedback}. You must plan the sections based on the human feedback."
            if human_feedback and human_feedback != 'no'
            else ''
        )

        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=self.USER_PROMPT.format(
                topic=topic,
                requirements=requirements,
                today=today,
                initial_research=docs_content,
                max_sections=max_sections,
                feedback_instruction=feedback_instruction
            ))
        ]

        try:
            response = self._invoke_model(messages)

            logger.info(f"PlannerAgent: title: {response.title}; sections: {
                        [s.title for s in response.sections]}")

            return {"title": response.title, "sections": response.sections, "date": response.date}

        except Exception as e:
            logger.error(f"Error during planning: {str(e)}")
            raise e
            # return {"title": "", "sections": [], "date": ""}
