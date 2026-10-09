from abc import ABC, abstractmethod
from stage3_vector_store.models.search_result import SearchResult
class Reranker(ABC):
    @abstractmethod
    def rerank(
        self,
        query: str,
        search_results: list[SearchResult],
        top_k: int
    ) -> list[SearchResult]:
        ...