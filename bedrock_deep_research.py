import logging
import os
import uuid
from datetime import datetime
from typing import List

import pyperclip
import pytz
import streamlit as st
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from bedrock_deep_research import BedrockDeepResearch
from bedrock_deep_research.config import DEFAULT_TOPIC, SUPPORTED_MODELS, Configuration
from bedrock_deep_research.model import Section
from bedrock_deep_research.utils import CustomError

logger = logging.getLogger(__name__)
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()


default_st_vals = {
    "head_image_path": None,
    "bedrock_deep_research": None,
    "stage": "initial_form",
    "article": "",
    "text_error": "",
}


class Article(BaseModel):
    title: str = Field(description="Title of the article")
    sections: List[Section] = Field(
        description="List of sections in the article")

    def render_outline(self) -> str:
        """Render the article outline."""
        sections_content = "\n".join(
            f"**{i + 1}. {section.name}**\n\n{section.description}\n" for i, section in enumerate(self.sections)
        )
        return f"### {self.title}\n\n{sections_content}"

    def render_section(self, section: Section) -> str:
        """Render a single section."""
        return f"\n## {section.name}\n\n{section.content}"

    def render_full_article(self) -> str:
        """Render the full article with all sections."""
        sections_content = "\n".join(
            self.render_section(section) for section in self.sections
        )
        return (
            f"# {self.title}\n#### Date: {self._get_date_today()}\n\n{sections_content}"
        )

    @staticmethod
    def _get_date_today() -> str:
        """Get today's date in UTC."""
        return datetime.now(pytz.UTC).strftime("%Y-%m-%d")

    def __str__(self) -> str:
        """String representation of the article."""
        return self.render_outline()


def init_state():

    for key, default_st_val in default_st_vals.items():
        if key not in st.session_state:
            st.session_state[key] = default_st_val


def render_initial_form():
    """
    Renders the initial form for article generation with topic and writing_guidelines inputs.
    """
    try:
        with st.form("article_form"):
            topic = st.text_area(
                "Topic",
                value=DEFAULT_TOPIC,
                help="Enter the topic you want to write about",
            )

            writing_guidelines = st.text_area(
                "Writing Guidelines",
                value=Configuration.writing_guidelines,
                help="Enter any specific guidelines regarding the writing length and style",
            )

            planner_model_name = st.selectbox(
                "Select your Model for planning tasks", SUPPORTED_MODELS.keys()
            )

            writer_model_name = st.selectbox(
                "Select your Model for writing tasks", SUPPORTED_MODELS.keys()
            )

            number_of_queries = st.number_input(
                "Number of queries generated for each web search",
                min_value=1,
                max_value=5,
                value=Configuration.number_of_queries,
            )

            max_search_depth = st.number_input(
                "Maximum number of reflection and web search iterations allowed for each sections",
                min_value=1,
                max_value=5,
                value=Configuration.max_search_depth,
            )

            submitted = st.form_submit_button(
                "Generate Outline", type="primary")

            if submitted:
                logger.info(
                    f"generate_article on '{topic}' following '{writing_guidelines}'"
                )

                if not topic:
                    st.session_state.text_error = "Please enter a topic"
                    return

                if not writing_guidelines:
                    st.session_state.text_error = (
                        "Please enter your writing guidelines for the article"
                    )
                    return

                config = {
                    "configurable": {
                        "thread_id": str(uuid.uuid4()),
                        "writing_guidelines": writing_guidelines,
                        "max_search_depth": max_search_depth,
                        "number_of_queries": number_of_queries,
                        "planner_model": SUPPORTED_MODELS.get(planner_model_name),
                        "writer_model": SUPPORTED_MODELS.get(writer_model_name),
                    }
                }

                st.session_state.bedrock_deep_research = BedrockDeepResearch(
                    config=config, tavily_api_key=os.getenv("TAVILY_API_KEY")
                )

                with st.session_state.text_spinner_placeholder:
                    with st.spinner(
                        "Please wait while the article outline is being generated..."
                    ):
                        try:
                            response = st.session_state.bedrock_deep_research.start(
                                topic)
                        except CustomError as e:
                            logger.error(f"Bedrock ClientError: {e}")
                            raise e

                        except Exception as e:
                            logger.error(
                                f"An error occurred while creating the outline: {e}")
                            raise e
                        else:
                            logger.debug(f"Outline response: {response}")
                            state = st.session_state.bedrock_deep_research.get_state()

                            article = Article(
                                title=state.values["title"],
                                sections=state.values["sections"],
                            )
                            st.session_state.article = article.render_outline()
                            st.session_state.stage = "outline_feedback"
                            st.rerun()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


def render_outline_feedback(article_container):
    """
    Renders the article outline and gets user feedback.
    """
    with article_container.container():
        st.markdown("## Article Outline")
        st.markdown(st.session_state.article)

    st.markdown("Please provide feedback to the outline")

    with st.form("feedback_form"):

        feedback = st.text_area(
            label="Feedback",
            placeholder="Input a feedback to change the title or the sections",
        )

        col1, col2 = st.columns(2)

        with col1:
            submit_feedback_pressed = st.form_submit_button("Submit Feedback")

            if submit_feedback_pressed:
                on_submit_button_click(feedback)

        with col2:
            accept_outline_pressed = st.form_submit_button(
                "Accept Outline", type="primary"
            )

            if accept_outline_pressed:
                on_accept_outline_button_click()


def render_final_result(article_container):
    """
    Renders the final article with options to copy or start over.
    """

    logger.info("render_final_result")
    logger.info(st.session_state)

    with article_container.container():
        if "head_image_path" in st.session_state and st.session_state.head_image_path:
            st.image(st.session_state.head_image_path, width=1200)

        st.markdown(st.session_state.article)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Copy to Clipboard", type="primary"):
            st.write("Article copied to clipboard!")
            st.toast("Article copied to clipboard!")
            pyperclip.copy(st.session_state.article)

    with col2:
        if st.button("Start Over"):
            st.session_state.bedrock_deep_research = None
            st.session_state.stage = "initial_form"

            st.rerun()

    # Display any error messages
    if st.session_state.text_error:
        st.error(st.session_state.text_error)


def on_submit_button_click(feedback):
    try:
        logger.info("Submit feedback pressed")
        if not feedback:
            st.session_state.text_error = "Please enter a feedback"
            return

        with st.session_state.text_spinner_placeholder:
            with st.spinner("Please wait while your feedback is being processed"):
                try:
                    response = st.session_state.bedrock_deep_research.feedback(
                        feedback)

                    logger.info(f"Feedback response: {response}")

                    state = st.session_state.bedrock_deep_research.get_state()

                    article = Article(
                        title=state.values["title"], sections=state.values["sections"]
                    )

                    st.session_state.article = article.render_outline()
                    st.session_state.text_error = ""
                    st.rerun()
                except Exception as e:
                    st.error(
                        f"An error occurred while processing feedback: {e}")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        st.error(f"An error occurred: {e}")


def on_accept_outline_button_click():
    logger.info("Accept outline pressed")

    try:
        # if st.form_submit_button("Accept Outline", type="primary"):
        with st.session_state.text_spinner_placeholder:
            with st.spinner("Please wait while the article is being generated..."):
                try:
                    response = st.session_state.bedrock_deep_research.feedback(
                        True)

                    logger.info(f"Accept outline response: {response}")

                    state = st.session_state.bedrock_deep_research.get_state()

                    st.session_state.head_image_path = state.values["head_image_path"]
                    st.session_state.article = state.values["final_report"]

                    st.session_state.stage = "final_result"
                    st.session_state.text_error = ""
                    st.rerun()
                except Exception as e:
                    st.error(f"An error occurred in article creation: {e}")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        st.error(f"An error occurred: {e}")


def main():

    load_dotenv()
    init_state()

    logging.basicConfig(
        level=LOGLEVEL,
        force=True,
        format="%(levelname)s:%(filename)s:L%(lineno)d - %(message)s",
    )

    # Header
    title_container = st.container()
    col1, col2 = st.columns([1, 5])
    with title_container:
        with col1:
            st.image("static/bedrock-icon.png", width=100)
        with col2:
            st.title("Bedrock Deep Researcher")

    st.divider()

    # Main stage
    st.session_state.text_spinner_placeholder = st.empty()
    article_placeholder = st.empty()

    if st.session_state.stage == "initial_form":
        render_initial_form()
    elif st.session_state.stage == "outline_feedback":
        render_outline_feedback(article_placeholder)
    elif st.session_state.stage == "final_result":
        render_final_result(article_placeholder)


if __name__ == "__main__":
    main()
