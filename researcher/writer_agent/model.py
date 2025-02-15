from typing import List, Optional, TypedDict

from langchain_core.documents import Document
from pydantic import BaseModel, Field


class Section(BaseModel):
    title: str
    content: Optional[str] = None
    documents: Optional[List[Document]] = []
    references: Optional[List[str]] = []


class ResearchState(TypedDict):
    task: dict
    refined_search_query: str
    initial_research: List[Document]
    sections: List[Section]
    human_feedback: str
    # Report layout
    title: str
    headers: dict
    date: str
    table_of_contents: str
    problem_statement: str
    introduction: str
    conclusions: str
    sources: List[str]
    final_report: str
    number_of_queries: int
    initial_research_input_tokens: int
    initial_research_output_tokens: int
    initial_research_execution_time: float


class ResearchMetadata(BaseModel):
    input_tokens: int = Field(
        default=0, description="The number of input tokens")
    output_tokens: int = Field(
        default=0, description="The number of output tokens")
    execution_time_in_seconds: float = Field(
        default=0, description="The execution time in seconds"
    )


class ResearchResults(BaseModel):
    query: str = Field(description="The original query")
    sub_queries: Optional[List[str]] = Field(
        default=[], description="The sub queries used to answer the original query"
    )
    documents: List[Document] = Field(
        default=[], description="The documents retrieved from the search queries"
    )
    metadata: ResearchMetadata = Field(
        default=ResearchMetadata(), description="Metadata about the research"
    )
