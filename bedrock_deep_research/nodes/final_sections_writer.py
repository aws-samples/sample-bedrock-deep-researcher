from botocore.exceptions import ClientError
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from ..config import Configuration
from ..model import Section, SectionState
from ..utils import exponential_backoff_retry

final_section_writer_instructions = """You are an expert technical writer crafting a section that synthesizes information from the rest of the article.

<Section title>
{section_title}
</Section title>

<Section description>
{section_description}
</Section description>

<Available article content>
{context}
</Available article content>

<Task>
1. Section-Specific Approach:

For Introduction:
- Do not include a section title
- 50-100 word limit
- Write in simple and clear language
- Focus on the core motivation for the article in 1-2 paragraphs
- Use a clear narrative arc to introduce the article
- Include NO structural elements (no lists or tables)
- No sources section needed

For Conclusion/Summary:
- Do not include a section title
- 100-150 word limit
- For comparative articles:
    * Must include a focused comparison table using Markdown table syntax
    * Table should distill insights from the article
    * Keep table entries clear and concise
- For non-comparative articles:
    * Only use ONE structural element IF it helps distill the points made in the article:
    * Either a focused table comparing items present in the article (using Markdown table syntax)
    * Or a short list using proper Markdown list syntax:
      - Use `*` or `-` for unordered lists
      - Use `1.` for ordered lists
      - Ensure proper indentation and spacing
- End with specific next steps or implications
- No sources section needed

3. Writing Approach:
- Use concrete details over general statements
- Make every word count
- Focus on your single most important point
</Task>

<Quality Checks>
- Do not include any title or Markdown element starting with # or ##
- For introduction: 50-100 word limit, no structural elements, no sources section
- For conclusion: 100-150 word limit, only ONE structural element at most, no sources section
- Markdown format
- Do not include word count or any preamble in your response
</Quality Checks>"""


class FinalSectionsWriter:
    N = "write_final_sections"

    def __call__(self, state: SectionState, config: RunnableConfig):
        """Write final sections of the article, which do not require web search and use the completed sections as context"""

        section = state["section"]
        completed_report_sections = state["report_sections_from_research"]

        configurable = Configuration.from_runnable_config(config)

        writer_model = ChatBedrock(
            model_id=configurable.writer_model, streaming=True)

        section.content = self._generate_final_sections(
            writer_model,
            final_section_writer_instructions,
            section,
            completed_report_sections,
        )

        return {"completed_sections": [section]}

    @exponential_backoff_retry(ClientError, max_retries=10)
    def _generate_final_sections(
        self,
        model: ChatBedrock,
        system_prompt: str,
        section: Section,
        completed_report_sections: str,
    ) -> str:
        # Format system instructions
        system_instructions = system_prompt.format(
            section_title=section.name,
            section_description=section.description,
            context=completed_report_sections,
        )

        # Generate section
        section_content = model.invoke(
            [SystemMessage(content=system_instructions)]
            + [
                HumanMessage(
                    content="Generate a section of an article based on the provided sources."
                )
            ]
        )

        return section_content.content
