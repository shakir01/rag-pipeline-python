from abc import ABC, abstractmethod
from stage4_retrieval.filters.metadata_filter import MetadataFilter

class VectorStore(ABC):
    def __init__(self):
      super().__init__()

    @abstractmethod
    def add(self, embedded_chunks):
        pass

    @abstractmethod
    def search(self,query_embeddings, top_k, metadata_filter: MetadataFilter=None):
        pass

    @abstractmethod
    def delete(self, embedded_chunk):
        pass

    @abstractmethod
    def update(self,embed_chunk):
        pass