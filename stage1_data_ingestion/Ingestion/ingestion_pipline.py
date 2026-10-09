from ast import List
from importlib.resources import contents
from pathlib import Path
from pydoc import doc
import re
from typing import Any
import os
from datetime import datetime, timezone
from pandas.tests.scalar import timestamp
from stage1_data_ingestion.Ingestion.Chunkers.sentance_chunker import SentanceChunker
from stage1_data_ingestion.Ingestion.Parsers.csv_parser import CSVParser
from stage1_data_ingestion.Ingestion.Parsers.pdf_parser import PdfParser
from stage1_data_ingestion.Ingestion.Parsers.text_parser import TextParser
from stage1_data_ingestion.Ingestion.models import Document, FileMetadata
from stage1_data_ingestion.Ingestion.Chunkers.chunker import Chunker
from stage1_data_ingestion.Ingestion.Chunkers.chunking_pipline import ChunkingPipline
from stage1_data_ingestion.Ingestion.Parsers.docx_parser import DocxParser
from stage1_data_ingestion.Ingestion.Parsers.sheet_parser import SheetParser
from stage2_embedding import embedding_generator
from stage2_embedding.embedding_generator import EmbeddingGenerator
from stage3_vector_store.in_memory_vectore_store import InMemoryVectorStore
from stage4_retrieval.vector_retriever import RetrievalRequest, VectorRetriever
from stage4_retrieval.filters.metadata_filter import MetadataFilter
from stage4_retrieval.models.filter_condition import FilterCondition
from stage5_context_builder.context_builder import ContextBuilder
from stage6_prompt_builder.prompt_builder import PromptBuilder
from stage7_llm_generator.nova_lite_generator import NovaLiteGenerator
class IngestionPipeline:
	def __init__(self, root_path: Path):
		self.root_path = root_path
		self.parsers = {
			".txt": TextParser(),
			".csv": CSVParser(),
			".pdf":PdfParser(),
			".docx":DocxParser(),
			".xlsx":SheetParser(),
		}
		self.embedding_generator = EmbeddingGenerator("sentence-transformers/all-MiniLM-L6-v2")
		self.in_memory_vector_store = InMemoryVectorStore()  
		self.chunk_list = []     
		self.doc_dict = {}

	def get_in_memory_vector_store(self):
		return self.in_memory_vector_store

	def get_chunk_list(self):
		return self.chunk_list
	
	def allowed_file_for_embedding (self,file_type:str):
		if file_type == '.docx' or  file_type == '.text' or file_type == '.pdf' or file_type == '.csv':
			return True
		return False	

	def ingest(self, root_file_path: Path | None = None) -> Any:
		root_path = root_file_path or self.root_path
		#embedding_chunks =[]
		for dirpath, _, filenames in os.walk(root_path):
			for filename in filenames:
				file_path = os.path.join(dirpath, filename)
				parser = self.parsers.get(Path(filename).suffix.lower())
				#print('root_path', root_path, 'file_path', file_path, 'filename', filename, 'dirpath', dirpath, 'parser', parser)
				
				if parser is None:
					continue

				document = parser.parse(file_path)
				#print(f'parser returned data: {type(parser)} parsed_data:{type(parsed_data)}')
				filemetadata = self.parse_metadata(file_path)
				'''document: Document = Document(
    				content=parsed_data,
    				metadata=filemetadata,
				)'''
				self.doc_dict[filemetadata.file_name] = document
				#if type(document) == str:
				#print (f'ingestion pipline document type {type(document)} filename: {Path(filename).suffix.lower()}')
				document.metadata = filemetadata
				chunkingPipline = ChunkingPipline(document)
				
				chklist = chunkingPipline.process(document)
				self.chunk_list.extend(chklist)
				#print(f'chunk list: {chklist}')
				'''if Path(filename).suffix.lower() == '.csv':
					for item in chklist:
						print(f'csv chunk content: {item.content}')'''

				if self.allowed_file_for_embedding(Path(filename).suffix.lower()):
					embeddings = self.embedding_generator.generate_embeddings(chklist)
					self.in_memory_vector_store.add(embeddings)
					#print (f'embeddings: {embeddings}')
				#embedding_chunks.extend(embeddings)
				#if Path(filename).suffix.lower() == '.pdf':
				#	print(f'chunk list len: {len(chklist)} chunk:{chklist}')
				#chunker = SentanceChunker(document)
				#chunker.chunk(document)
				#print(f"self.doc_dict: {self.doc_dict}")
				#print (f"contents: {document.content}, MetaData:{document.metadata}")
				#print(f"Parsed data from {file_path}: {parsed_data}")
		return self.doc_dict, self.chunk_list, self.in_memory_vector_store
		

	def parse_metadata(self, file_path: Path) -> FileMetadata:
		try:
			metadata = FileMetadata.from_path(Path(file_path))
			return metadata
		except (FileNotFoundError, PermissionError, OSError) as error:
			print(f"Could not read metadata for {file_path}: {error}")
			return None

		#print (f"Metadata for {file_path}: {metadata.file_last_accessed}")

		#print(f"Metadata for {file_path}: {metadata_dict}")
		'''print(type(metadata))        # <class 'int'>
		print(type(metadata).__name__)  # int
		print('file_path', file_path, metadata)'''



		
