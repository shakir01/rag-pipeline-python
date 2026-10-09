from stage1_data_ingestion.Ingestion.Chunkers.pdf_chunker import PdfChunker
from stage1_data_ingestion.Ingestion.Chunkers.sentance_chunker import SentanceChunker
from stage1_data_ingestion.Ingestion.Chunkers.semantic_chunker import SemanticChunker
from stage1_data_ingestion.Ingestion.Chunkers.recursive_chunker import RecursiveChunker
from stage1_data_ingestion.Ingestion.Chunkers.paragraph_chunker import ParagraphChunker
from stage1_data_ingestion.Ingestion.Chunkers.image_chunker import ImageChunker
from stage1_data_ingestion.Ingestion.Chunkers.spreadsheet_chunker import SpreadSheetChunker
from stage1_data_ingestion.Ingestion.Chunkers.table_chunker import TableChunker

class ChunkerFactory:
    _chunkers = {
        "sentence": SentanceChunker,
        "semantic": SemanticChunker,
        "recursive": RecursiveChunker,
        "pdf": PdfChunker,
        "paragraph": ParagraphChunker,
        'spreadsheetChunker':SpreadSheetChunker,
        'tablechunker':TableChunker,
        'imagechunker':ImageChunker
    }


    @classmethod
    def get_chunker(cls, strategy):
        chunker_class = cls._chunkers.get(strategy)

        if chunker_class is None:
            raise ValueError(f"Unknown chunking strategy: {strategy}")

        return chunker_class()