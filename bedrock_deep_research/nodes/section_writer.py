import logging
from typing import List, Literal

from botocore.exceptions import ClientError
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END
from langgraph.types import Command
from pydantic import BaseModel, Field

from ..config import Configuration
from ..model import Section, SectionState
from ..utils import exponential_backoff_retry
from .section_web_researcher import SectionWebResearcher

logger = logging.getLogger(__name__)


class Feedback(BaseModel):
    """A feedback for a section with potential followup queries."""

    grade: Literal["pass", "fail"] = Field(
        description="Evaluation result indicating whether the response meets requirements ('pass') or needs revision ('fail')."
    )
    follow_up_queries: List[str] = Field(
        description="List of follow-up search queries.",
    )


# Section writer instructions
section_writer_instructions = """You are an expert technical writer crafting one section of a technical article.

<Section topic>
{section_topic}
</Section topic>

<Existing section content (if populated)>
{section_content}
</Existing section content>

<Source material>
{context}
</Source material>

<Guidelines for writing>
1. If the existing section content is not populated, write a new section from scratch.
2. If the existing section content is populated, write a new section that synthesizes the existing section content with the new information.
</Guidelines for writing>

<Length and style>
- Do not include a section title
- No marketing language
- Technical focus
- Write in simple, clear language
- Use short paragraphs (2-3 sentences max)
- Only use ONE structural element IF it helps clarify your point:
  * Either a focused table comparing 2-3 key items (using Markdown table syntax)
  * Or a short list (3-5 items) using proper Markdown list syntax:
    - Use `*` or `-` for unordered lists
    - Use `1.` for ordered lists
    - Ensure proper indentation and spacing
- End with ### Sources that references the below source material formatted as:
  * List each source with title, date, and URL
  * Format: `- Title : URL`
{writing_guidelines}
</Length and style>

<Quality checks>
- Careful use of only ONE structural element (table or list) and only if it helps clarify your point
- One specific example / case study
- No preamble prior to creating the section content
- Sources cited at end
</Quality checks>
"""

# Instructions for section grading
section_grader_instructions = """Review a section of an article relative to the specified topic:

<section topic>
{section_topic}
</section topic>

<section content>
{section}
</section content>

<task>
Evaluate whether the section adequately covers the topic by checking technical accuracy and depth.

If the section fails any criteria, generate specific follow-up search queries to gather missing information.
</task>

<format>
    grade: Literal["pass","fail"] = Field(
        description="Evaluation result indicating whether the response meets requirements ('pass') or needs revision ('fail')."
    )
    follow_up_queries: List[SearchQuery] = Field(
        description="List of follow-up search queries.",
    )
</format>
"""


class SectionWriter:
    """Write a section of the article"""

    N = "section_write"

    def __call__(self, state: SectionState, config: RunnableConfig) -> Command[Literal[END, SectionWebResearcher.N]]:
        """Write a section of the article"""

        # Get state
        section = state["section"]
        source_str = state["source_str"]
        sources = state["sources"]

        # Get configuration
        configurable = Configuration.from_runnable_config(config)
        writing_guidelines = configurable.writing_guidelines

        try:
            writer_model = ChatBedrock(
                model_id=configurable.writer_model, max_tokens=configurable.max_tokens)

            section.content = self._generate_section_content(
                writer_model,
                section_writer_instructions,
                section,
                source_str,
                writing_guidelines,
            )
            section.sources = sources

            feedback = self._grade_section_content(
                writer_model, section_grader_instructions, section
            )

        except Exception as e:
            logger.error(f"Error writing section: {e}")
            raise e

        if (
            feedback.grade == "pass"
            or state["search_iterations"] >= configurable.max_search_depth
        ):
            # Publish the section to completed sections
            return Command(update={"completed_sections": [section]}, goto=END)
        else:
            # Update the existing section with new content and update search queries
            return Command(
                update={
                    "search_queries": feedback.follow_up_queries,
                    "section": section,
                },
                goto=SectionWebResearcher.N,
            )

    @exponential_backoff_retry(ClientError, max_retries=10)
    def _generate_section_content(
        self,
        model: ChatBedrock,
        system_prompt: str,
        section: Section,
        search_content: str,
        writing_guidelines: str,
    ) -> str:
        system_prompt = system_prompt.format(
            section_title=section.name,
            section_topic=section.description,
            context=search_content,
            section_content=section.content,
            writing_guidelines=writing_guidelines,
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content="Generate a section of the article based on the provided sources."
            ),
        ]

        section_content = model.invoke(messages)

        return section_content.content

    @exponential_backoff_retry(ClientError, max_retries=10)
    def _grade_section_content(
        self, model: ChatBedrock, system_prompt: str, section: Section
    ) -> Feedback:

        section_grader_instructions_formatted = system_prompt.format(
            section_topic=section.description, section=section.content
        )

        structured_llm = model.with_structured_output(Feedback)
        feedback = structured_llm.invoke(
            [SystemMessage(content=section_grader_instructions_formatted)]
            + [
                HumanMessage(
                    content="Grade the article and consider follow-up questions for missing information:"
                )
            ]
        )

        return feedback
