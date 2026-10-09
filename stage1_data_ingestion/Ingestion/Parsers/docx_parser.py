from sys import meta_path
from docx import Document
from stage1_data_ingestion.Ingestion import models
import os
class DocxParser:
    def __init__(self):
        pass

    def parse(self, file_path) -> models.Document:
        # Open the .docx file
        doc = Document(file_path)
        list_paragraphs = []
        document = models.Document()
        # Iterate through each paragraph and print its text
        for paragraph in doc.paragraphs:
            # Optional: skip blank lines
            if paragraph.text.strip():
                document.paragraph_list.append(paragraph)
                #print(paragraph.text)
        return document