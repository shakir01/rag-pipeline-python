from dataclasses import dataclass, field

@dataclass
class Chunk:
    content: str = ''
    document_id: str = ''
    chunk_id: int = 0
    chunk_index:int = 0
    metadata: dict = field(default_factory=dict)