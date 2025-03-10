import logging
import os
import uuid

import pyperclip
import streamlit as st
from dotenv import load_dotenv

from bedrock_deep_research import BedrockDeepResearch
from bedrock_deep_research.config import (DEFAULT_TOPIC, SUPPORTED_MODELS,
                                          Configuration)

logger = logging.getLogger(__name__)
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()


default_st_vals = {
    "messages": [],
    "topic": "",
    "outline_msg": "",
    "head_image_path": None,
    "bedrock_deep_research": None,
    "stage": "initial_form",
    "article": "",
    "text_error": "",
}


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
            st.session_state.topic = st.text_area(
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
                    f"generate_article on '{st.session_state.topic}' following '{writing_guidelines}'"
                )

                if not st.session_state.topic:
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
                    with st.spinner("Please wait while the article outline is being generated..."):
                        result = st.session_state.bedrock_deep_research.start(
                            st.session_state.topic)

                        state = st.session_state.bedrock_deep_research.get_state()

                        last_message = state.values["messages"][-1]

                        logger.info(
                            f"render_initial_form: Last message: {last_message.content}")
                        st.markdown(
                            last_message.content + "\n**Please provide feedback on the article outline or type 'ok' to proceed with the writing**")

                        st.session_state.messages.append(
                            {"role": "assistant", "content": last_message.content})

                        # for item in result:
                        #     if isinstance(item, dict) and '__interrupt__' in item:
                        #         interrupt_obj = item['__interrupt__']
                        #         st.session_state.messages = [
                        #             {"role": "assistant", "content": interrupt_obj[0].value}]
                        #         break

                        st.session_state.stage = "outline_feedback"
                        st.rerun()

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


def render_outline_feedback():
    """
    Renders the article outline and gets user feedback.
    """
    # message = st.chat_message("assistant")

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # message.write(st.session_state.outline_msg)

    if prompt := st.chat_input():
        with st.chat_message("user"):
            st.write(prompt)

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            try:
                response = st.session_state.bedrock_deep_research.feedback(
                    prompt)
                # logger.info(f"Stream: {s.content}")
                logger.info(f"Response {response}")

                state = st.session_state.bedrock_deep_research.get_state()

                last_message = state.values["messages"][-1]

                logger.info(f"outline: Last message: {last_message.content}")

                if 'head_image_path' in state.values and state.values['head_image_path']:
                    st.image(state.values['head_image_path'])

                st.markdown(last_message.content)
                st.session_state.messages.append(
                    {"role": "assistant", "content": last_message.content})
            except Exception as e:
                logger.error(
                    f"An error occurred during feedback processing: {str(e)}")
                st.error(
                    "An error occurred while processing your request. Please try again.")

            # for item in response:
            #     if isinstance(item, dict) and '__interrupt__' in item:
            #         interrupt_obj = item['__interrupt__']
            #         st.markdown(interrupt_obj[0].value)
            #         st.session_state.messages.append(
            #             {"role": "assistant", "content": interrupt_obj[0].value})
            #         break
            #     elif isinstance(item, dict) and 'compile_final_article' in item:
            #         final_report = item['compile_final_article']['final_report']

            #         st.markdown(final_report)
            #         if st.button("Copy to Clipboard", type="primary"):
            #             st.toast("Article copied to clipboard!")
            #             pyperclip.copy(final_report)

            #         st.session_state.messages.append(
            #             {"role": "assistant", "content": final_report})


def main():

    load_dotenv()
    init_state()
# amazonq-ignore-next-line

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

    if st.session_state.stage == "initial_form":
        render_initial_form()
    elif st.session_state.stage == "outline_feedback":
        render_outline_feedback()

    # if st.button("Start Over"):
    #     st.session_state.bedrock_deep_research = None
    #     st.session_state.stage = "initial_form"

    #     st.rerun()


if __name__ == "__main__":
    main()
