from dataclasses import dataclass,field
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk

@dataclass
class EmbeddedChunk:
    chunk: Chunk = None
    embedding: list[float] = field(default_factory=list)

