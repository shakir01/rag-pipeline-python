from abc import ABC, abstractmethod
from stage1_data_ingestion.Ingestion.models import Document
import os

class DocumentParser(ABC):
    @abstractmethod
    def parse(self, file_path) -> Document:
        pass
