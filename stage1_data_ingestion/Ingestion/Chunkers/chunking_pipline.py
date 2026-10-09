from ast import List
from typing import Self
from stage1_data_ingestion.Ingestion.Chunkers import semantic_chunker, spreadsheet_chunker, table_chunker
from stage1_data_ingestion.Ingestion.Chunkers import recursive_chunker
from stage1_data_ingestion.Ingestion.Chunkers.pdf_chunker import PdfChunker
from stage1_data_ingestion.Ingestion.models import Document
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk
from stage1_data_ingestion.Ingestion.Chunkers.sentance_chunker import SentanceChunker
from stage1_data_ingestion.Ingestion.Chunkers.chunking_factory import ChunkerFactory, SpreadSheetChunker
from stage1_data_ingestion.Ingestion.Chunkers.table_chunker import TableChunker
from stage1_data_ingestion.Ingestion.Chunkers.semantic_chunker import SemanticChunker
from stage1_data_ingestion.Ingestion.Chunkers.recursive_chunker import RecursiveChunker
from stage1_data_ingestion.Ingestion.Chunkers.docx_chunker import DocxChunker

class ChunkingPipline:
    def __init__(self, document:Document):
        self.documnet = document
        #print('Chunking pipline:',document)
        self.recursive_chunking_flag = True


    def process(self, document) -> list:
        chunlist = []
        print(f'process input argument document type: {type(document)}')
        if document.metadata.file_extension == '.txt':
            sentanceChunker = SentanceChunker(document)
            chunlist = sentanceChunker.chunk(document)
        elif document.metadata.file_extension == '.csv':
            tableChunker = TableChunker(document)
            chunlist = tableChunker.chunk(document)
            #print('chunk list: ',chunlist)
        elif document.metadata.file_extension == '.pdf':
            pdf_chunker = PdfChunker(document)
            chunlist = pdf_chunker.chunk(document)
            #print('pdf chunker')
        elif document.metadata.file_extension == '.docx':
                '''if self.recursive_chunking_flag == True:
                    recursive_chunker = RecursiveChunker (document)
                    chunlist     = recursive_chunker.chunk(document)
                else:
                    docx_chunker = DocxChunker (document)
                    chunlist     = docx_chunker.chunk(document)'''
                if self.recursive_chunking_flag:
                    recursive_chunker = RecursiveChunker(
                        max_chunk_size=500,
                        overlap=10,
                        chunk_size_tolrance=20
                    )
                    chunlist = recursive_chunker.chunk(document)
                else:
                    docx_chunker = DocxChunker()
                    chunlist = docx_chunker.chunk(document)
        elif document.metadata.file_extension == '.xlsx':
            spreadsheet_chunker = SpreadSheetChunker(document)
            chunlist = spreadsheet_chunker.chunk(document)
        '''
        elif document.metadata.file_extension == '.docx':
            pass
            #semantic_chunker = SemanticChunker (document)'''
        #if len(chunlist) == 1:
        #print('chun list: ',len(chunlist), ' document extension ', document.metadata.file_name)
        if document.metadata.file_extension == '.docx':
            #print(f'chunk list: {chunlist}')
            for chunk in chunlist:
                #(f'chunk details: {chunk}\n\n')
                pass
        return chunlist