from typing import TYPE_CHECKING, Any

from stage5_context_builder.context_build_model import ContextItem
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk

if TYPE_CHECKING:
    from stage3_vector_store.vector_store_model import VectorSearchResult
else:
    VectorSearchResult = Any

class ContextBuilder:
    def __init__(self):
        self.context_items:dict[tuple[int, int], ContextItem] = {}

    def  add_retrieved_results (self,retrieved_results: list[VectorSearchResult]):
        for result in retrieved_results:
            self.context_items[(result.embedded_chunk.chunk.chunk_id, result.embedded_chunk.chunk.document_id)] = (ContextItem(chunk=result.embedded_chunk.chunk,similarity_score=result.similarity_score))

    def get_context_items(self):
        return list(self.context_items.values())

    def get_context_item_for_chunk(self,chunk:Chunk):
        key = (chunk.chunk_id, chunk.document_id)
        if key not in self.context_items:
            raise KeyError(
            f"Configuration error: Key '{(key)}' not found in context_items."
        )
      
        return self.context_items[key]
      
    def get_context_items_for_document(self, document_id):
        document_context_items = [
            context_item
            for (chnk_id, doc_id), context_item in self.context_items.items()
            if doc_id == document_id
        ]
        return document_context_items

    '''
    ContextItems
    ↓
    for each item
        ↓
    extract:
        chunk.content
        chunk.metadata
        chunk.document_id
        chunk.chunk_id
        ↓
    format
        ↓
    join
        ↓
    context string
    '''
    def build_context(self):
        context_str_list = []
        for (chunk_id, document_id), context_item in self.context_items.items():
            source = context_item.chunk.metadata.get('filename', 'Unknown')
            context_str_list.append( f"{context_item.chunk.content} [Chunk: {chunk_id},source:{source}] ")            
        context_str = '\n\n'.join(context_str_list)
        return context_str

         
