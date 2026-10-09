from dataclasses import dataclass, field
from stage4_retrieval.filters.metadata_filter import MetadataFilter
@dataclass
class RetrievalRequest:
    query: str
    top_k: int = 5
    metadata_filter: MetadataFilter | None = None