from pydoc import Doc

from stage1_data_ingestion.Ingestion.Parsers.document_parser import DocumentParser
from stage1_data_ingestion.Ingestion.models import Document
import os

class TextParser(DocumentParser):
	def parse(self, file_path) -> Document:
		try:
			with open(file_path, encoding="cp1252") as file:
				document = Document()
				document.content = file.read()
				return document
		except UnicodeDecodeError:
			with open(file_path, encoding="utf-8") as file:
				return file.read()