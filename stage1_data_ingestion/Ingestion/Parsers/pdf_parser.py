from sys import meta_path

from stage1_data_ingestion.Ingestion.Parsers.document_parser import DocumentParser
from stage1_data_ingestion.Ingestion.models import Document
import os
from PyPDF2 import PdfReader

class PdfParser(DocumentParser):
    def parse(self, file_path) -> Document:
        reader = PdfReader(file_path)

        #meta_data = reader.metadata
        # print(f'meta_data: {meta_data}')
        #print(f'meta_data-----? author: {meta_data.author} title:{meta_data.title}, subject: {meta_data.subject}, size: {meta_data.s}')
        pdf_all_pages_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pdf_all_pages_text += text
        document = Document()
        document.content = pdf_all_pages_text
        return document