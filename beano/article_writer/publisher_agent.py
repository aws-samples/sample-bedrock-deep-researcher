import logging
import sys
from datetime import datetime

from .utils import write_text_to_md

logger = logging.getLogger(__name__)


class PublisherAgent:
    def run(self, state: dict) -> dict:
        logging.info(f"PublisherAgent.run:")

        title = state.get("title")
        date = state.get("date")
        introduction = state.get("introduction")
        conclusions = state.get("conclusions")
        sections = ""
        references = ""
        filename = (
            datetime.now().strftime("%Y%m%d") + "-" + title.replace(" ", "-") + ".md"
        )
        for s in state.get("sections"):
            sections += f"\n{s.content}\n"
            # sections += f"\n## {s.title}\n{s.content}\n"

            for r in s.references:
                references += f"\n- {r}"

        layout = f"""# {title}
#### Date: {date}

## Introduction
{introduction}

{sections}

## Conclusions
{conclusions}

## References
{references}
"""
        write_text_to_md(filename, "reports", layout)

        return {"final_report": layout}
