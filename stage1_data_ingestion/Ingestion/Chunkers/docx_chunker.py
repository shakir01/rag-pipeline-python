from sys import meta_path
from docx import Document
from stage1_data_ingestion.Ingestion.Chunkers.chunker import Chunker
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk
from stage1_data_ingestion.Ingestion.models import Document
from stage1_data_ingestion.Ingestion import models
import os

class DocxChunker (Chunker):
    def __init__(self,document:Document):
        super().__init__()

    def chunk (self,document:Document) -> list:
        # Split by 2 or more newline characters (with optional spaces/tabs between them)
               para_list = document.paragraph_list
               # Usage
               chunk_list = []
               index = 0
               for para in para_list:
                  chnk = Chunk()
                  chnk.chunk_id = Chunker.chunk_Id()
                  chnk.content = para.text
                  chnk.metadata['filename'] = document.metadata.file_name
                  chnk.metadata['extension'] = document.metadata.file_extension
                  chnk.metadata['owner'] = document.metadata.file_owner
                  chnk.chunk_index = index
                  index += 1
                  chunk_list.append(chnk) 
               return chunk_list
