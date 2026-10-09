from dataclasses import dataclass

from stage2_embedding.embedding_model import EmbeddedChunk
from stage5_context_builder.context_builder import Chunk
@dataclass
class VectorSearchResult:
    embedded_chunk: EmbeddedChunk
    similarity_score: float

