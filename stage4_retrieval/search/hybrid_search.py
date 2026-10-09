from operator import index

from stage3_vector_store.in_memory_vectore_store import InMemoryVectorStore, VectorSearchResult
from stage4_retrieval.search.keyword_search import KeywordSearch
from stage4_retrieval.search.search_strategy import SearchResult

class HybridSearch:
    def __init__(self, vector_store: InMemoryVectorStore, keyword_search: KeywordSearch):
        self.vector_store = vector_store
        self.keyword_search = keyword_search
        self.vector_search_results: list[VectorSearchResult] = []
        self.keyword_search_results: list[SearchResult] = []
    def initialize_search_results(self, vector_search_results: list[VectorSearchResult], keyword_search_results: list[SearchResult]):
        self.vector_search_results = vector_search_results
        self.keyword_search_results = keyword_search_results

    def match_found_in_list(self, chunk_id: int) -> tuple[bool, SearchResult,int| None]:
        for result in self.keyword_search_results:
            if result.chunk.id == chunk_id:
                index = self.keyword_search_results.index(result)   
                return True, result, index
        return False, None, None

def rerank(self, top_k: int ) -> list[SearchResult]:
        # Combine the results from both searches    
        search_results: list[SearchResult] = []
        semantic_results_not_matched = []
        keywords_matched_with_semantic_results = []
        for result in self.vector_search_results:
            search_item_exists, existing_result, index = self.match_found_in_list(result.chunk.id)
            if search_item_exists:
                search_results.append(SearchResult(chunk=result.chunk, hybrid_score=( 0.7*result.similarity_score + 0.3*existing_result.score)))
                keywords_matched_with_semantic_results.append(index)
            else:
                semantic_results_not_matched.append(SearchResult(chunk=result.chunk, hybrid_score=result.similarity_score))

        for i in range(len(self.keyword_search_results)):
            if i not in keywords_matched_with_semantic_results:
                search_results.append(SearchResult(chunk=self.keyword_search_results[i].chunk, hybrid_score=self.keyword_search_results[i].score))
        
        search_results.extend(semantic_results_not_matched)
        search_results.sort(key=lambda x: x.hybrid_score, reverse=True) 
        return search_results[:top_k]
    