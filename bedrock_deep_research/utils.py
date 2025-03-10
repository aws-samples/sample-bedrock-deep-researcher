import logging
import random
import re
import time
from functools import wraps

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class CustomError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


def exponential_backoff_retry(
    ExceptionToCheck, max_retries: int = 5, initial_delay: float = 1.0
):
    """
    Decorator that implements exponential backoff retry logic.

    Args:
        func: Function to retry
        ExceptionToCheck: Exception class to check for retrying
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ExpiredTokenException':
                        logger.error(
                            "Expired token error. Please check/update your Security Token included in the request")
                        # Do not try max_retry times
                        attempt = max_retries
                        raise CustomError(
                            message="Expired Token. Please update the AWS credentials, to connect to the boto Client.")
                    elif e.response['Error']['Code'] == 'ThrottlingException':
                        if attempt == max_retries:
                            logger.error(
                                f"Error code: {e.response['Error']['Code']}"
                                f"Execution failed after {max_retries} attempts due to throttling. Try again later.")
                            raise CustomError(
                                message=f"Throttling Exception raised.. Retry limit of {max_retries} retries reached.")
                        logger.info(
                            f"Attempt {attempt+1} failed due to throttling. Retrying...")
                        # Add jitter to avoid thundering herd problem
                        jitter = random.uniform(0, 0.1 * delay)
                        sleep_time = delay + jitter
                        logger.debug(
                            f"Retrying in {sleep_time:.2f} seconds..."
                        )
                        time.sleep(sleep_time)
                        delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"Client Error Raised: {e}")
                        raise e
                except ExceptionToCheck as e:
                    logger.error(f"Error raised by {func.__name__}: {e}")
                    raise e
        return wrapper

    return decorator


def format_web_search(search_response, max_tokens_per_source, include_raw_content=True):
    # Format output
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(search_response, 1):
        formatted_text += f"Source {source['title']}:\n===\n"
        formatted_text += f"URL: {source['url']}\n===\n"
        formatted_text += (
            f"Most relevant content from source: {source['content']}\n===\n"
        )
        if include_raw_content:
            # Using rough estimate of 4 characters per token
            char_limit = max_tokens_per_source * 4
            # Handle None raw_content
            raw_content = source.get("raw_content", "")
            if raw_content is None:
                raw_content = ""
                logger.warning(
                    f"Warning: No raw_content found for source {source['url']}")
            if len(raw_content) > char_limit:
                raw_content = raw_content[:char_limit] + "... [truncated]"
            formatted_text += f"Full source content limited to {max_tokens_per_source} tokens: {raw_content}\n\n"

    return formatted_text.strip()


def extract_xml_content(text: str, tag_name: str) -> str | None:
    pattern = f"<{tag_name}>(.*?)</{tag_name}>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        return None
