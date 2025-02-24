import os
from dataclasses import dataclass, fields
from typing import Any, List, Optional

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.runnables import RunnableConfig

DEFAULT_REPORT_STRUCTURE = """The report structure should focus on breaking-down the user-provided topic:

1. Introduction (no research needed)
   - Brief overview of the topic area

2. Main Body Sections:
   - Each section should focus on a sub-topic of the user-provided topic
   - Include any key concepts and definitions
   - Provide real-world examples or case studies where applicable

3. Conclusion
   - Aim for 1 structural element (either a list of table) that distills the main body sections
   - Provide a concise summary of the report"""


@dataclass(kw_only=True)
class Configuration:
    """The configurable fields for the chatbot."""
    report_structure: str = DEFAULT_REPORT_STRUCTURE
    writing_guidelines: str = """
- Strict 200 word limit
- Start with your most important insight in **bold**
"""
    number_of_queries: int = 2  # Number of search queries to generate per iteration
    max_search_depth: int = 2  # Maximum number of reflection + search iterations
    planner_model: str = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    writer_model: str = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    output_dir: str = "output"

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values: dict[str, Any] = {
            f.name: os.environ.get(f.name.upper(), configurable.get(f.name))
            for f in fields(cls)
            if f.init
        }

        return cls(**{k: v for k, v in values.items() if v})
