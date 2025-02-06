from abc import ABC
from enum import Enum
from typing import List, Optional, Set

from pydantic import BaseModel

from ..object_factory import ObjectFactory


class RetrieverType(Enum):
    GOOGLE = "Google"
    TAVILY = "Tavily"
    DUCK = "DuckDuckGo"

    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class RetrieverResult(BaseModel):
    title: str
    content: str
    url: str
    retriever: RetrieverType
    require_scraping: bool


class RetrieverResults(BaseModel):
    query: str
    parent_query: str = Optional[str]
    results: List[RetrieverResult]

    def urls(self) -> List[str]:
        return list({result.url for result in self.results})


class RetrieverProvider(ObjectFactory):
    def get(self, service_id, **kwargs):
        return self.create(service_id, **kwargs)


class RetrieverService(ABC):
    def __init__(self, service_id):
        self.service_id = service_id

    def search(self, query, **kwargs) -> List[RetrieverResult]:
        pass
