from dataclasses import dataclass,field
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk
import numpy as np
from numpy import ndarray
@dataclass
class SearchResult:
    chunk: Chunk
    semantic_score: float | None = None
    keyword_score: float | None = None
    hybrid_score: float | None = None
    rerank_score: float | None = None

