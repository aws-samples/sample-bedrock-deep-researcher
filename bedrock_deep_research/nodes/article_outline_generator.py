import json
import logging

from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from ..config import Configuration
from ..model import ArticleState, Outline

logger = logging.getLogger(__name__)

system_prompt = """You are an expert technical writer tasked to plan an article outline for a topic.

<instructions>
1. Create a clear, engaging title for the article
2. Generate a list of sections for the article.
3. Design a logical progression of sections with descriptive headings
4. Each section should have the fields:
    - name: Concise, descriptive section heading
    - section_number: Sequential integer for ordering
    - description: Brief summary of section content (2-3 sentences)
    - research: Boolean value (true/false) indicating if web research is needed
    - content: Empty string (to be filled later)
5. Introduction and conclusion will not require research because they can distill information from other parts of the article.
6. If a feedback is provided, use it to improve the outline or the title.
7. Return the title and sections as a valid JSON object without any additional text.
</instructions>
"""
user_prompt_template = """
The topic of the article is:
<topic>
{topic}
</topic>

<article organization>
{article_organization}
</article organization>

Use this context to plan the sections of the article:
<Context>
{context}
</Context>

<feedback>
{feedback}
</feedback>
"""


class ArticleOutlineGenerator:
    N = "generate_article_outline"

    async def __call__(self, state: ArticleState, config: RunnableConfig):
        logging.info("Generating report plan")

        topic = state.get("topic", "")
        source_str = state.get("source_str", "")
        feedback = state.get("feedback_on_report_plan", "")
        if feedback:
            feedback = f"<Feedback>\nHere is some feedback on article structure from user review:{feedback}\n</Feedback>"

        configurable = Configuration.from_runnable_config(config)

        user_prompt = user_prompt_template.format(
            topic=topic,
            article_organization=configurable.report_structure,
            context=source_str,
            feedback=feedback,
        )
        outline_response = self.generate_outline(
            configurable.planner_model, configurable.max_tokens, system_prompt, user_prompt)

        outline_obj = json.loads(outline_response.content)

        logger.info(f"Outline json: {outline_obj}")

        outline = Outline.model_validate(outline_obj, strict=True)

        logger.info(f"Generated sections: {outline.sections}")

        return {"title": outline.title, "sections": outline.sections}

    def generate_outline(self, model_id: str, max_tokens: int, system_prompt: str, user_prompt: str):

        planner_model = ChatBedrock(
            model_id=model_id, max_tokens=max_tokens)
        # ).with_structured_output(Outline)

        return planner_model.invoke(
            [SystemMessage(content=system_prompt)]
            + [
                HumanMessage(
                    content=user_prompt
                )
            ]
        )
