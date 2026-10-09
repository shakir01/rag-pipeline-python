from stage1_data_ingestion.Ingestion.Chunkers.chunker import Chunker
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk
from stage1_data_ingestion.Ingestion.models import Document
import csv
from io import StringIO


class TableChunker(Chunker):
    def __init__(self,document:Document):
        super().__init__()
        self.document = document

    def chunk(self, document: Document) -> list[Chunk]:
        content = document.content
        reader = csv.reader(StringIO(content))
        header = next(reader)
        chunksList = []
        index = 0
        for row in reader:
            index += 1
            ch1 = Chunk()
            result = " ".join(row)
            ch1.content = result
            ch1.chunk_id = Chunker.chunk_Id()
            ch1.document_id = document.metadata.file_id
            ch1.metadata['filename'] = document.metadata.file_name
            ch1.metadata['extension'] = document.metadata.file_extension
            ch1.metadata['owner'] = document.metadata.file_owner
            chunksList.append(ch1)
            #print(ch1)

        return chunksList