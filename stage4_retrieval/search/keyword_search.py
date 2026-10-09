from stage4_retrieval.search.search_strategy import SearchResult, SearchStrategy
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk
from stage4_retrieval.filters.metadata_filter import MetadataFilter

class KeywordSearch(SearchStrategy):
    def tokenize(self, text: str) -> list[str]:
        # Simple word based tokenizer
        return text.split()

    def search(
        self,
        query: str,
        chunks: list[Chunk],
        top_k: int,
        metadata_filter: MetadataFilter | None = None,
    ) -> list[SearchResult]:
        # Tokenize the query
        query_tokens = set(self.tokenize(query.lower()))

        results = []
        for chunk in chunks:
            # Apply metadata filter only if provided
            if metadata_filter is not None:
                if not metadata_filter.matches(chunk.metadata):
                    continue

            # Tokenize the chunk text
            chunk_tokens = set(self.tokenize(chunk.text.lower()))

            # Calculate keyword score based on token overlap
            overlap = query_tokens.intersection(chunk_tokens)
            keyword_score = len(overlap) / len(query_tokens) if query_tokens else 0

            results.append(SearchResult(chunk=chunk, keyword_score=keyword_score))

        # Sort results by keyword score in descending order and return top_k results
        results.sort(key=lambda x: x.keyword_score, reverse=True)
        return results[:top_k]