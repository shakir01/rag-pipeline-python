from stage4_retrieval.filters.metadata_filter import FilterCondition, MetadataFilter
from stage4_retrieval.retriever import Retriever
from stage2_embedding.embedding_generator import EmbeddingGenerator
from stage3_vector_store.vector_store import VectorStore
from stage4_retrieval.models.retrieval_request import RetrievalRequest
class VectorRetriever(Retriever):
    def __init__(self, embedding_generator, vector_store):
        super().__init__()
        self.embedding_generator = embedding_generator
        self.vector_store = vector_store
        
    def retrieve(self, retrieval_request: RetrievalRequest):
        query_embedding = (
            self.embedding_generator.generate_embedding(retrieval_request.query)
        )

        results = self.vector_store.search(
            query_embedding,
            retrieval_request.top_k,
            retrieval_request.metadata_filter
        )

        return results