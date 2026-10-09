from stage1_data_ingestion.Ingestion.Chunkers.chunker import Chunker
from stage1_data_ingestion.Ingestion.models import Document
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk
from PyPDF2 import PdfReader

class PdfChunker (Chunker):
    def __init__(self,document:Document):
        super().__init__()

    def chunk (self,document:Document):
        #print(f'chunk (self,document:Document): {document.content}')
        sentances = document.content.split('.')
        sentances_list = []
        chunk_list = []
        index = 0

        for sentance in sentances:
            if sentance.strip(): 
                sentances_list.append(sentance.strip())

        for sentance in sentances_list:
            chunk_item = Chunk()
            chunk_id = Chunker.chunk_Id()
            chunk_item.chunk_id = chunk_id
            chunk_item.content = sentance
            chunk_item.metadata['filename'] = document.metadata.file_name
            chunk_item.metadata['extension'] = document.metadata.file_extension
            chunk_item.metadata['owner'] = document.metadata.file_owner
            chunk_list.append(chunk_item)
            chunk_item.chunk_index = index
            index += 1
        return chunk_list
        