import os
import random
import time
import uuid
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def exponential_backoff_retry(
    ExceptionToCheck, max_retries: int = 5, initial_delay: float = 1.0
):
    """
    Decorator that implements exponential backoff retry logic.

    Args:
        func: Function to retry
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

                except ExceptionToCheck as e:

                    if attempt == max_retries:
                        logger.error(f"Execution failed after {attempt} attempts")
                        raise e

                    # Add jitter to avoid thundering herd problem
                    jitter = random.uniform(0, 0.1 * delay)
                    sleep_time = delay + jitter

                    logger.debug(
                        f"Attempt {attempt + 1}/{max_retries} failed. {str(e)}"
                        f"Retrying in {sleep_time:.2f} seconds..."
                    )

                    time.sleep(sleep_time)
                    delay *= 2  # Exponential backoff

        return wrapper

    return decorator


def write_text_to_md(filename: str, path: str, text: str) -> str:
    # Generate unique task ID
    task = uuid.uuid4().hex
    file_path = f"{path}/{filename}.md"

    # Create directory if it doesn't exist
    os.makedirs(path, exist_ok=True)

    # Write text to markdown file
    with open(file_path, "w") as f:
        f.write(text)

    return file_path
