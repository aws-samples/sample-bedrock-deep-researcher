import operator
from typing import Annotated, List, TypedDict

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Query for web search.")


class Queries(BaseModel):
    """A list of search queries"""

    queries: List[str] = Field(description="List of search queries.")


class Source(BaseModel):
    title: str = Field(description="Title of the source.")
    url: str = Field(description="URL of the source.")


class Section(BaseModel):
    section_number: int = Field(
        description="Number of the section used to sort the section in the final article."
    )

    name: str = Field(
        description="Name for this section of the report.",
    )
    description: str = Field(
        description="Brief overview of the main topics and concepts to be covered in this section.", default=""
    )
    research: bool = Field(
        description="Whether to perform web research for this section of the report.", default=True
    )
    content: str = Field(description="The content of the section.", default="")
    sources: List[Source] = Field(
        description="List of sources for this section.", default=[]
    )


class OutlineSection(BaseModel):
    name: str = Field(
        description="Name for this section of the report.",
    )
    description: str = Field(
        description="Brief overview of the main topics and concepts to be covered in this section.",
    )


class Outline(BaseModel):
    """A outline of the research article"""

    title: str = Field(
        description="Title of the article.",
    )
    sections: List[OutlineSection] = Field(
        description="Sections of the article.",
    )


class ArticleState(TypedDict):
    topic: str
    title: str
    sections: list[Section]
    completed_sections: Annotated[list, operator.add]
    # String of any completed sections from research to write final sections
    report_sections_from_research: str
    source_str: str  # String of formatted source content from web search

    feedback_on_report_plan: str
    final_report: str
    head_image_path: str


class ArticleInputState(TypedDict):
    topic: str


class ArticleOutputState(TypedDict):
    final_report: str


class SectionState(TypedDict):
    section: Section  # Report section
    search_iterations: int  # Number of search iterations done
    search_queries: list[SearchQuery]  # List of search queries
    sources: Annotated[list, operator.add]
    source_str: str  # String of formatted source content from web search
    feedback_on_report_plan: str  # Feedback on the report plan
    # String of any completed sections from research to write final sections
    report_sections_from_research: str
    # Final key we duplicate in outer state for Send() API
    completed_sections: list[Section]


class SectionOutputState(TypedDict):
    # Final key we duplicate in outer state for Send() API
    completed_sections: list[Section]
