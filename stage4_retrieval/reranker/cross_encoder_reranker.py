from sentence_transformers import CrossEncoder
from stage4_retrieval.reranker.reranker import Reranker
from stage4_retrieval.search.keyword_search import SearchResult

class CrossEncoderReranker(Reranker):
    def __init__(self):
        self.model_name = 'cross-encoder/ms-marco-MiniLM-L-6-v2'
        self.cross_encoder_model = CrossEncoder(self.model_name) 

    def rerank(self, query: str, search_results: list[SearchResult], top_k: int) -> list[SearchResult]:
        # Prepare the input for the cross-encoder model
        cross_encoder_input = [(query, result.chunk) for result in search_results]

        # Get the relevance scores from the cross-encoder model
        relevance_scores = self.cross_encoder_model.predict(cross_encoder_input)

        # Update the search results with the new relevance scores
        for i, result in enumerate(search_results):
            result.rerank_score = relevance_scores[i]

        # Sort the search results based on the new relevance scores
        search_results.sort(key=lambda x: x.rerank_score, reverse=True)

        return search_results[:top_k]