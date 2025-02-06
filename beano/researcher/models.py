from typing import List, Optional

from langchain_core.documents import Document
from pydantic import BaseModel, Field, field_validator

from .retrievers import RetrieverType


class DeepSearchQueries(BaseModel):
    queries: List[str]


class ResearchMetadata(BaseModel):
    input_tokens: int = Field(default=0, description="The number of input tokens")
    output_tokens: int = Field(default=0, description="The number of output tokens")
    execution_time_in_seconds: float = Field(
        default=0, description="The execution time in seconds"
    )
    scraped_documents: int = Field(
        default=0, description="The number of scraped documents"
    )
    cached_documents: int = Field(
        default=0, description="The number of documents read from cache"
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


class ResearcherConfig(BaseModel):
    aws_region: str = "us-east-1"
    llm_model_id: str
    embedding_model_id: str = "amazon.titan-embed-text-v1"
    retrievers: List[str]
    retrievers_config: dict = {}

    # @field_validator('retrievers')
    # @classmethod
    # def validate_retrievers(cls, v):
    #     valid_retrievers = [RetrieverType.TAVILY,
    #                         RetrieverType.DUCK, RetrieverType.GOOGLE]
    #     if not all(r in valid_retrievers for r in v):
    #         raise ValueError(f"Retrievers must be one of {valid_retrievers}")
    #     return v


# class Section(BaseModel):
#     title: str
#     content: str
#     references: List[str]


# class Report(BaseModel):
#     title: str
#     date: str
#     introduction: str
#     sections: List[Section]
#     conclusion: str
#     references: List[str]

#     def to_markdown(self) -> str:
#         """Convert the report to markdown format."""
#         sections_text = self._format_sections()
#         references_text = self._format_references()

#         return f"""# {self.title}
# #### Date: {self.date}

# ## Introduction
# {self.introduction}

# {sections_text}

# ## Conclusions
# {self.conclusion}

# ## References
# {references_text}
# """

#     def _format_sections(self) -> str:
#         """Format all sections into markdown."""
#         return "\n".join(
#             f"## {section.title}\n{section.content}"
#             for section in self.sections
#         )

#     def _format_references(self) -> str:
#         """Format all references into markdown list."""
#         return "\n".join(f"- {ref}" for ref in self.references)
