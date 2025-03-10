import base64
import io
import json
import logging
import time
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from PIL import Image

from bedrock_deep_research.utils import exponential_backoff_retry

from ..config import Configuration
from ..model import ArticleState

logger = logging.getLogger(__name__)


class ImageError(Exception):
    "Custom exception for errors returned by Amazon Nova Canvas"

    def __init__(self, message):
        self.message = message


@exponential_backoff_retry(Exception, max_retries=10)
def generate_image(model_id, body):
    """
    Generate an image using Amazon Nova Canvas model on demand.
    Args:
        model_id (str): The model ID to use.
        body (str) : The request body to use.
    Returns:
        image_bytes (bytes): The image generated by the model.
    """
    bedrock = boto3.client(
        service_name="bedrock-runtime", config=Config(read_timeout=300)
    )

    accept = "application/json"
    content_type = "application/json"

    response = bedrock.invoke_model(
        body=body, modelId=model_id, accept=accept, contentType=content_type
    )
    response_body = json.loads(response.get("body").read())

    base64_image = response_body.get("images")[0]
    base64_bytes = base64_image.encode("ascii")
    image_bytes = base64.b64decode(base64_bytes)

    finish_reason = response_body.get("error")

    if finish_reason is not None:
        raise ImageError(f"Image generation error. Error is {finish_reason}")

    logger.info(
        "Successfully generated image with model %s", model_id
    )

    return image_bytes


generate_image_prompt = """You are an expert prompt engineer tasked to create a prompt to generate the head image of an article.

<Task>
Generate a prompt used to generate the head image of an article. Use the title and the article outline as context

The prompt must explain that the image should be catchy, high-quality and realistic.
You must only return the prompt string and nothing else.
</Task>

<Article title>
{title}
</Article title>

<Article outline>
{outline}
</Article outline>
"""


class ArticleHeadImageGenerator:
    N = "generate_head_image"

    def __call__(self, state: ArticleState, config: RunnableConfig):
        title = state["title"]
        sections = state["completed_sections"]
        # Article ID comprises of first 4 words of the title and a hex timestamp in str format
        # Title is capped to 40 chars to keep the length in check
        article_id = ("_".join(title.split(" ")[:4])[:40] +
                      "_" + hex(int(time.time()))[2:])

        image_path = ""
        try:
            configurable = Configuration.from_runnable_config(config)

            planner_model = ChatBedrock(
                model_id=configurable.planner_model, max_tokens=configurable.max_tokens)

            system_prompt = generate_image_prompt.format(
                title=title, outline="\n".join(f"- {s.name}" for s in sections)
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content="Create a prompt to generate the main image of the article"
                ),
            ]

            prompt = planner_model.invoke(messages)

            logger.info("Generated head image prompt: %s", prompt.content)

            body = json.dumps(
                {
                    "taskType": "TEXT_IMAGE",
                    "textToImageParams": {"text": prompt.content},
                    "imageGenerationConfig": {
                        "numberOfImages": 1,
                        "height": 640,
                        "width": 1200,
                        "cfgScale": 8.0,
                        "seed": 0,
                    },
                }
            )

            image_bytes = generate_image(
                model_id=configurable.image_model, body=body)
            image_path = self._save_image(
                article_id, configurable.output_dir, image_bytes
            )

        except ClientError as err:
            message = err.response["Error"]["Message"]
            logger.error("A bedrock client error occurred:", message)
        except Exception as e:
            logger.error(

                "An error occurred during ArticleHeadImageGenerator:", e)

        logger.info("Generated head image: %s", image_path)
        return {"head_image_path": image_path}

    def _save_image(self, article_id, output_dir, image_bytes) -> None:
        try:

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            report_path = Path(f"{output_dir}/{article_id}")
            report_path.mkdir(parents=True, exist_ok=True)

            image_path = report_path / f"{article_id}.png"

            with Image.open(io.BytesIO(image_bytes)) as image:
                image.save(image_path, format="PNG")

            return image_path
        except ImageError as err:
            logger.error(

                f"Error saving the generated image results: {err.message}")
