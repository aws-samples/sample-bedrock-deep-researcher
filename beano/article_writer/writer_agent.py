import logging

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from .model import Section
from .utils import exponential_backoff_retry

logger = logging.getLogger(__name__)


class IntroductionConclusionSection(BaseModel):
    introduction: str
    conclusions: str


class WriterAgent:

    SYSTEM_PROMPT = (
        "You are an expert technical writer."
        "Make sure that the flow of the whole article is consistent and easy to follow. "
        "Use the following user requirements to generate the article: "
        "<requirements>{requirements}</requirements>"
    )
    SECTION_USER_PROMPT = (
        "Your task is to write a section of an article titled '{article_title}'. "
        "The content of the section must be based exclusively on the provided research data and related to the title of the section. "
        "The document should be well structured, complete, informative, in-depth, and comprehensive, with facts and numbers. "
        "You MUST produce the document in {format} format "
        "You MUST NOT generate the title, only the section content. "
        "You must write a section at the time using the provided section title and the research data for this section."
        "The generated document must NOT include title, introduction, conclusion and references."
        "Generate only the text, do NOT include any title"
        "section title: {section_title}"
        "section research data: {research_data}"
    )

    INTRO_PROMPT_OPTIMIZED = """
Task: Write an introduction and a conclusion section for the following article text enclosed in <article> tags.
The topic of the article is enclosed in <topic> tags.
The introduction should provide an overview of the main topic and key points that will be covered in the article.
Instructions:
1. Read the article text carefully to understand its content and main themes.
2. Identify the central topic or subject that the article focuses on.
3. Determine the key points, arguments, or information that the article aims to convey.
4. In the introduction write 3-5 concise paragraphs that:
    - Introduce the main topic or subject of the article
    - Provide relevant background or context to help readers understand the topic
    - Outline the key points or arguments that will be discussed in the article
    - Avoid including the title of the article or any section headings
    - Keep it brief but informative, aiming to engage the reader's interest in the article's content.
5. In the conclusion section write 3-5 concise paragraphs that:
    - Restates the main idea or thesis in a clear and concise way
    - Summarizes the key supporting points and arguments
    - Provides a final perspective or insight on the topic
    - Does not introduce any new information not present in the original article
    - Keep the conclusion focused, avoiding unnecessary repetition or details.
6. Format your output as a JSON object with the following fields:
{{"introduction": [Your introduction here], "conclusions": [Your conclusions here]}}

Topic:
<topic>
{topic}
</topic>

Article text:
<article>
{article}
</article>
"""

    def __init__(self, model):
        self.model = model
        self.messages = []

    @exponential_backoff_retry(Exception)
    def _invoke_model(self, messages):
        """Invoke the model with retry logic for ServiceUnavailableError."""
        return self.model.invoke(messages)

    @exponential_backoff_retry(Exception)
    def _invoke_model_intro(self, messages) -> IntroductionConclusionSection:
        """Invoke the model with retry logic for ServiceUnavailableError."""
        return self.model.with_structured_output(IntroductionConclusionSection).invoke(
            messages
        )

    def run(self, state: dict):
        logger.info(f"WriterAgent.run:")
        task = state["task"]
        article_title = state["title"]
        topic = task["topic"]
        requirements = task["requirements"]
        sections = state["sections"]

        format = task.get("format", "markdown")

        self.messages = [
            SystemMessage(content=self.SYSTEM_PROMPT.format(requirements=requirements))
        ]

        sections = [
            self._process_section(article_title, section, format)
            for section in sections
        ]

        results = self._invoke_model_intro(
            [
                HumanMessage(
                    content=self.INTRO_PROMPT_OPTIMIZED.format(
                        topic=topic,
                        article="\n\n".join([section.content for section in sections]),
                    )
                )
            ]
        )

        return {
            "sections": sections,
            "introduction": results.introduction,
            "conclusions": results.conclusions,
        }

    def _process_section(self, article_title: str, section: Section, format: str):
        references = []
        section_title = section.title
        research_data = ""

        logger.debug(f"Processing section: {section_title}")

        for document in section.documents:
            document_content = document.page_content
            source = document.metadata.get("source")
            document_title = document.metadata.get("title", "")
            research_data += "\n\n" + "\n".join(
                [
                    f"Source Document: {document_title}",
                    f"Source Content: {document_content}",
                ]
            )

            references.append(source)

        self.messages.append(
            HumanMessage(
                content=self.SECTION_USER_PROMPT.format(
                    article_title=article_title,
                    section_title=section_title,
                    research_data=research_data,
                    format=format,
                )
            )
        )
        response = self._invoke_model(self.messages)
        self.messages.append(response)
        section.content = response.content
        section.references = references
        return section
