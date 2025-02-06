from .duckduckgo import DuckDuckGoServiceBuilder
from .google import GoogleServiceBuilder
from .retrievers import RetrieverProvider, RetrieverResults, RetrieverType
from .tavily import TavilyServiceBuilder

retriever_service_provider = RetrieverProvider()

retriever_service_provider.register_builder(
    RetrieverType.TAVILY, TavilyServiceBuilder()
)
retriever_service_provider.register_builder(
    RetrieverType.DUCK, DuckDuckGoServiceBuilder()
)
retriever_service_provider.register_builder(
    RetrieverType.GOOGLE, GoogleServiceBuilder()
)

__all__ = ["RetrieverType", "ResearchResults" "retriever_service_provider"]
