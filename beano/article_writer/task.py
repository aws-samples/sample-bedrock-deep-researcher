from typing import List, Optional

from pydantic import BaseModel


class Task(BaseModel):
    topic: str
    requirements: str
    max_sections: int = 5
    writing_guidelines: Optional[str] = None
