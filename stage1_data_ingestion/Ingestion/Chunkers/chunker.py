from abc import ABC, abstractmethod
from typing import Any, ClassVar, Self

class Chunker (ABC):
    _chunk_id = -1

    @abstractmethod
    def chunk (self, document):
        pass

    @classmethod
    def chunk_Id (cls):
        cls._chunk_id += 1
        return cls._chunk_id
