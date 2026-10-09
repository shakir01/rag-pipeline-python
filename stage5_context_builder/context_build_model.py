from dataclasses import dataclass,field
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk

@dataclass
class ContextItem:
    chunk: Chunk
    similarity_score: float