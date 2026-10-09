from hashlib import file_digest
from webbrowser import get

from stage1_data_ingestion.Ingestion.ingestion_pipline import ContextBuilder, IngestionPipeline
from application.rag_pipline.rag_pipline import CrossEncoderReranker, KeywordSearch, PromptBuilder, RAGPipeline
from stage4_retrieval import retriever
from stage4_retrieval.filters.metadata_filter import FilterCondition, MetadataFilter
from stage4_retrieval.models.retrieval_request import RetrievalRequest
from stage4_retrieval.reranker import reranker
from stage4_retrieval.search import hybrid_search
from stage4_retrieval.vector_retriever import RetrievalRequest, VectorRetriever

try:
    from stage5_llm.nova_lite_generator import NovaLiteGenerator
except ImportError:
    class NovaLiteGenerator:
        def __init__(self, *args, **kwargs):
            pass

        def generate(self, prompt):
            return ""

class Application:
    def __init__(self):
        self.ingestion_pipeline = IngestionPipeline()
        self.doc_dict, self.chunk_list, self.in_memory_vector_store = self.ingestion_pipeline.ingest()
        if not self.chunk_list and not self.in_memory_vector_store:
            raise ValueError("Ingestion pipeline did not produce any chunks or vector store.")
        vector_retriever = VectorRetriever()
        self.llm_generator = NovaLiteGenerator()
        context_build = ContextBuilder()
        cross_encoder_reranker = CrossEncoderReranker()
        self.keyword_search = KeywordSearch()
        self.max_top_k = 1000
        self.max_top_k = self.get_max_top_k()
        self.hybrid_search = hybrid_search.HybridSearch(self.in_memory_vector_store, self.keyword_search) 
        self.prompt_builder = self.get_prompt()
        self.rag_pipeline = RAGPipeline(self.chunk_list, self.in_memory_vector_store, self.llm_generator,vector_retriever,context_build,cross_encoder_reranker,self.keyword_search,self.hybrid_search,self.prompt_builder)

    def get_max_top_k(self):
        max_top_k = input("Enter the maximum number of top results to retrieve (default value is 3): ")
        if not max_top_k:
            return 3
        try:
            max_top_k = int(max_top_k)
            if max_top_k <= 0:
                raise ValueError("Max Top K must be a positive integer.")
                return max_top_k
            elif max_top_k > 1000:
                print("Max Top K cannot exceed 1000. Setting to 1000.")
                return 1000
    
        except ValueError:
            print("Invalid input. Please enter a positive integer.")
            return self.get_max_top_k() 
        
    def get_prompt(self) -> str:
        prompt = (
        "Please answer the following question based on the context provided. "
        'If the answer is not contained within the context, '
        'please respond with "I don\'t know."'
        )
        
        prompt = input(f"Generated prompt:\n{prompt}\n\nDo you want to modify the prompt? (y/n): ")
        if prompt.lower() == 'y':
            prompt = input("Enter your modified prompt: ")
        return prompt
    
    def start(self):
        while True:
            query = input("Ask a question: ")

            if query.lower() == "exit":
                break
            metadata_filter = self.get_metadata_filter()
            top_k = self.get_top_k()
            answer = self.rag_pipeline.run(query, metadata_filter, top_k)
            print("\nAnswer:")
            print(answer)

    def get_top_k(self):
        top_k = input("Enter the number of top results to retrieve (default value is 3): ")
         
        if not top_k:
            return 3
        try:
            top_k = int(top_k)
            if top_k <= 0:
                raise ValueError("Top K must be a positive integer.")
            elif top_k > self.max_top_k:
                print(f"Top K cannot exceed {self.max_top_k}. Setting to {self.max_top_k}.")
                return self.max_top_k
            
            return top_k
        except ValueError:
            print("Invalid input. Please enter a positive integer.")
            return self.get_top_k()

    def get_metadata_filter(self):
        filtering_conditions = []
        file_types = input(
            "Enter file types (comma-separated, optional): "
        )

        if file_types:
            file_types = [
                file_type.strip()
                for file_type in file_types.split(",")
            ]

            filtering_conditions.append(
                FilterCondition(
                    field="source_type",
                    operator="in",
                    value=file_types
                )
            )

        file_name_contains = input(
            "Enter filename contains (optional): "
        ).strip()

        if file_name_contains:
            filtering_conditions.append(
                FilterCondition(
                    field="filename",
                    operator="contains",
                    value=file_name_contains
                )
            )

        if not filtering_conditions:
            return None

        return MetadataFilter(filtering_conditions)

    