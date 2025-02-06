# constants.py
import logging

import pyperclip
import streamlit as st
from dotenv import load_dotenv

from beano.article_writer import Task, TechnicalWriter
from beano.callbacks import get_streamlit_cb
from beano.model import Article, BedrockModel
from beano.researcher.retrievers.retrievers import RetrieverType

DEFAULT_MODEL_ID = "us.anthropic.claude-3-haiku-20240307-v1:0"
DEFAULT_MAX_SECTIONS = 3
DEFAULT_TOPIC = "Upload files using s3 presigned url"
DEFAULT_REQUIREMENTS = "Provide a detailed explanation and python code samples"

logger = logging.getLogger("beano")


class StateManager:
    def __init__(self):
        self.reset()

    @property
    def task(self):
        return st.session_state.task

    @task.setter
    def task(self, value):
        st.session_state.task = value

    @property
    def writer(self):
        return st.session_state.writer

    @writer.setter
    def writer(self, value):
        st.session_state.writer = value

    @property
    def stage(self):
        return st.session_state.stage

    @stage.setter
    def stage(self, value):
        st.session_state.stage = value

    def reset(self):
        if "writer" not in st.session_state:
            self.writer = None
        if "stage" not in st.session_state:
            st.session_state.stage = "initial_form"
        if "article" not in st.session_state:
            st.session_state.article = ""
        if "text_error" not in st.session_state:
            st.session_state.text_error = ""
        if "accept_draft" not in st.session_state:
            st.session_state.accept_draft = False
        if "cb_handler" not in st.session_state:
            st.session_state.cb_handler = None
        if "task" not in st.session_state:
            st.session_state.task = None


def render_initial_form(state_manager: StateManager, text_spinner_placeholder):
    """
    Renders the initial form for article generation with topic and requirements inputs.
    """
    with st.form("article_form"):
        topic = st.text_area(
            "Topic",
            value=DEFAULT_TOPIC,
            help="Enter the topic you want to write about"
        )

        requirements = st.text_area(
            "Requirements",
            value=DEFAULT_REQUIREMENTS,
            help="Enter any specific requirements for the article"
        )

        max_sections = st.number_input(
            "Maximum number of sections",
            min_value=1,
            max_value=10,
            value=DEFAULT_MAX_SECTIONS
        )

        retriever = st.selectbox(
            'Select your Search Engine', RetrieverType.list())

        model_id = st.selectbox(
            'Select your Model', BedrockModel.list_inference_profiles(), format_func=lambda x: BedrockModel.get_by_model_id(x).value
        )

        submitted = st.form_submit_button("Generate Article", type="primary")

        if submitted:
            logger.info(f"generate_article on '{
                topic}' following '{requirements}'")

            logger.info(f"Using model: {model_id}")
            logger.info(f"Using retriever: {retriever}")
            if not topic:
                st.session_state.text_error = "Please enter a topic"
                return

            if not requirements:
                st.session_state.text_error = "Please enter your requirements for the article"
                return

            state_manager.writer = TechnicalWriter(
                model_id=model_id,
                retriever=RetrieverType(retriever)
            )

            state_manager.task = Task(
                topic=topic,
                max_sections=max_sections,
                requirements=requirements
            )

            with text_spinner_placeholder:
                with st.spinner("Please wait while the article outline is being generated..."):
                    response = state_manager.writer.run(
                        task=state_manager.task,
                        task_id="1",
                        callables=[st.session_state.cb_handler]
                    )

                    article = Article(
                        title=response.get('title'),
                        sections=response.get('sections'),
                        date=response.get('date'),
                        introduction="",
                        conclusions=""
                    )

                    st.session_state.article = article.render_outline()
                    state_manager.stage = "outline_feedback"
                    st.rerun()


def render_outline_feedback(state_manager: StateManager, article_container, text_spinner_placeholder):
    """
    Renders the article outline and gets user feedback.
    """

    with article_container.container():
        st.markdown("## Article Outline")
        st.markdown(st.session_state.article)

    st.markdown("Please provide feedback to the outline")
    draft_feedback = st.text_area(
        label="Feedback", placeholder="Input a feedback to change the title or the sections")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Submit Feedback"):
            if not draft_feedback:
                st.session_state.text_error = "Please enter a feedback"
                return

            with text_spinner_placeholder:
                with st.spinner("Please wait while the article is being generated..."):
                    response = state_manager.writer.provide_human_plan_feedback(
                        task_id="1", human_feedback=draft_feedback, callables=[st.session_state.cb_handler])

                    article = Article(
                        title=response.get('title'),
                        sections=response.get('sections'),
                        date=response.get('date'),
                        introduction="",
                        conclusions=""
                    )

                    st.session_state.article = article.render_outline()
                    st.session_state.text_error = ""
                    st.rerun()

    with col2:
        if st.button("Accept Outline"):
            with text_spinner_placeholder:
                with st.status("Please wait while the article is being generated..."):
                    # with st.spinner("Please wait while the article is being generated..."):

                    while state_manager.writer.get_state(task_id="1").next:
                        response = state_manager.writer.provide_human_plan_feedback(
                            task_id="1", human_feedback="ok", callables=[st.session_state.cb_handler])

                    article = Article(
                        title=response.get('title'),
                        sections=response.get('sections'),
                        date=response.get('date'),
                        introduction=response.get(
                            'introduction'),
                        conclusions=response.get('conclusions')
                    )
                    st.session_state.article = article.render_full_article()
                    state_manager.stage = "final_result"
                    st.rerun()


def render_final_result(state_manager: StateManager, article_container, token_count_placeholder):
    """
    Renders the final article with options to copy or start over.
    """
    with token_count_placeholder.container():
        with st.expander("Metadata"):
            st.write(f"Input Tokens: {
                     state_manager.writer.token_counter.input_tokens}")
            st.write(f"Output Tokens: {
                     state_manager.writer.token_counter.output_tokens}")
            st.write(f"Words: {len(st.session_state.article.split())}")

    with article_container.container():
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
            state_manager.reset()
            st.rerun()

    # Display any error messages
    if st.session_state.text_error:
        st.error(st.session_state.text_error)

# main.py


def main():
    logging.basicConfig(level=logging.INFO, force=True,
                        format='%(levelname)s:%(name)s:%(filename)s:%(lineno)d:%(message)s')
    load_dotenv()

    state_manager = StateManager()

    st.title("Beano :writing_hand:")
    st.divider()

    text_spinner_placeholder = st.empty()
    token_count_placeholder = st.empty()
    article_placeholder = st.empty()
    st.session_state.cb_handler = get_streamlit_cb(
        article_placeholder.container())

    if state_manager.stage == "initial_form":
        render_initial_form(state_manager, text_spinner_placeholder)
    elif state_manager.stage == "outline_feedback":
        render_outline_feedback(
            state_manager, article_placeholder, text_spinner_placeholder)
    elif state_manager.stage == "final_result":
        render_final_result(
            state_manager, article_placeholder, token_count_placeholder)


if __name__ == "__main__":
    main()
