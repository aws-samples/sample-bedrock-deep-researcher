import operator
from datetime import datetime
from typing import Annotated, List, TypedDict

import pytz
from langgraph.graph.message import AnyMessage, add_messages
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
        description="Brief overview of the main topics and concepts to be covered in this section.",
    )
    research: bool = Field(
        description="Whether to perform web research for this section of the report."
    )
    content: str = Field(description="The content of the section.")
    sources: List[Source] = Field(
        description="List of sources for this section.", default=[]
    )


class Outline(BaseModel):
    """A outline of the research article"""

    title: str = Field(
        description="Title of the article.",
    )
    sections: List[Section] = Field(
        description="Sections of the article.",
    )

    def render_outline(self) -> str:
        sections_content = "\n".join(
            f"{i+1}. {section.name}" for i, section in enumerate(self.sections)
        )
        return f"\nTitle: {self.title}\n\n{sections_content}"


class Article(BaseModel):
    title: str = Field(description="Title of the article")
    date: str = Field(
        description="Date of the article",
        default=datetime.now(pytz.UTC).strftime("%Y-%m-%d"),
    )
    sections: List[Section] = Field(
        description="List of sections in the article")

    def render_section(self, section: Section) -> str:
        return f"\n## {section.name}\n\n{section.content}"

    def render_full_article(self) -> str:
        sections_content = "\n".join(
            self.render_section(section) for section in self.sections
        )
        return f"# {self.title}\n#### Date: {self.date}\n\n{sections_content}"


class ArticleState(TypedDict):
    article_id: str
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

    messages: Annotated[list[AnyMessage], add_messages]


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
