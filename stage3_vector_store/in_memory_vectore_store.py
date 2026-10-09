from stage2_embedding.embedding_model import EmbeddedChunk
from stage3_vector_store.models.vector_search_result import VectorSearchResult

from stage3_vector_store.vector_store import VectorStore
try:
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    def cosine_similarity(left, right):
        left = np.asarray(left, dtype=float)
        right = np.asarray(right, dtype=float)
        left_norm = np.linalg.norm(left, axis=1, keepdims=True)
        right_norm = np.linalg.norm(right, axis=1, keepdims=True)
        denominator = left_norm @ right_norm.T
        return np.divide(
            left @ right.T,
            denominator,
            out=np.zeros((left.shape[0], right.shape[0]), dtype=float),
            where=denominator != 0,
        )
import numpy as np

class InMemoryVectorStore(VectorStore):
    def __init__(self):
        super().__init__()
        self.embedding_chunks:EmbeddedChunk = []

    def add(self, embedded_chunks):
        self.embedding_chunks.extend(embedded_chunks)

    def search(self,query_embeddings, top_k, metadata_filter=None):
        similarity_list = []
        for embedding_item in self.embedding_chunks:
            
            query_vector = np.asarray(query_embeddings).reshape(1, -1)
            item_vector = np.asarray(embedding_item.embedding).reshape(1, -1)
            similarity = cosine_similarity(query_vector, item_vector)[0][0]
            #similarity_list.append((embedding_item,similarity))
            result = VectorSearchResult(
            embedded_chunk=embedding_item,
            similarity_score=float(similarity)
            )
            similarity_list.append(result)

        similarity_list.sort(key=lambda result: result.similarity_score,
        reverse=True)        
        return similarity_list[:top_k]

    def delete(self, embedded_chunk):
        pass

    def update(self,embed_chunk):
        pass