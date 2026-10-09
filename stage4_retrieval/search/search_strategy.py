from abc import ABC, abstractmethod
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk
from stage3_vector_store.models.search_result import SearchResult
from stage4_retrieval.filters.metadata_filter import MetadataFilter

class SearchStrategy(ABC):
    @abstractmethod
    def tokenize(self, text: str) -> list[str]:
        raise NotImplementedError("Subclasses must implement the tokenize method.")
    
    @abstractmethod
    def search(
        self,
        query: str,
        chunks: list[Chunk],
        top_k: int,
        metadata_filter: MetadataFilter | None = None,
    ) -> list[SearchResult]:
        raise NotImplementedError("Subclasses must implement the search method.")  
