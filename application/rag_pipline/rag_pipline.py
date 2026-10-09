
from stage3_vector_store import vector_store
from stage4_retrieval import vector_retriever
from stage4_retrieval.filters import metadata_filter
from stage4_retrieval.reranker.cross_encoder_reranker import CrossEncoderReranker
from stage4_retrieval.reranker.reranker import Reranker
from stage4_retrieval.search import hybrid_search
from stage4_retrieval.search.hybrid_search import KeywordSearch
from stage4_retrieval.search.keyword_search import SearchResult
from stage4_retrieval.vector_retriever import FilterCondition, MetadataFilter, RetrievalRequest, VectorRetriever
from stage5_context_builder.context_builder import ContextBuilder
from stage6_prompt_builder.prompt_builder import PromptBuilder
from stage7_llm_generator.nova_lite_generator import NovaLiteGenerator 

class RagPipeline:
    def __init__(self, chunk_list: list, in_memory_vector_store: vector_store.InMemoryVectorStore,llm_generator,vwector_retriever: VectorRetriever, context_builder: ContextBuilder, cross_encoder_reranker: CrossEncoderReranker, keyword_search: KeywordSearch, hybrid_search: hybrid_search.HybridSearch, prompt_builder: PromptBuilder):
      self.in_memory_vector_store = in_memory_vector_store
      self.chunk_list = chunk_list
      self.llm_generator = llm_generator
      self.vector_retriever = vector_retriever
      self.context_builder = context_builder
      self.cross_encoder_reranker = cross_encoder_reranker
      self.keyword_search = keyword_search
      self.hybrid_search = hybrid_search
      self.prompt_builder = prompt_builder

    def run(self, query: str,metadata_filter: MetadataFilter | None = None,top_k: int = 3) -> str:
        
        retriever_request = RetrievalRequest(query=query, top_k=top_k, metadata_filter=metadata_filter)        
        results = self.vector_retriever.retrieve(retriever_request)
       
        keyword_search_results = self.keyword_search.search(query, self.chunk_list, top_k=top_k, metadata_filter=metadata_filter)
        self.hybrid_search.initialize_search_results(results, keyword_search_results)   
        hybrid_search_results = self.hybrid_search.rerank(top_k=top_k)
        
        reranked_results = self.cross_encoder_reranker.rerank(query, hybrid_search_results, top_k=top_k)
        self.context_builder.add_retrieved_results(reranked_results)
        
        context_str = self.context_builder.build_context()
        prompt_str = self.prompt_builder.build_prompt(query,context_str)	
        print("========== FINAL PROMPT ==========")
        print(f'prompt_str: {prompt_str} context_str: {context_str}')
        print("==================================")
        answer = self.llm_generator.generate(prompt_str)
        print(f'LLM Output: {answer}	')

        #for result in results:
        #	print(f'result: {result.similarity_score}, results length: {len(results)}, prompt_str: {prompt_str}, context: {context_build.build_context()}')
        
        return answer