import csv
from stage1_data_ingestion.Ingestion.Parsers import document_parser
from stage1_data_ingestion.Ingestion.models import Document
class CSVParser(document_parser.DocumentParser):
    def parse(self, file_path):
        with open(file_path, newline="", encoding="utf-8-sig") as file:
            csv_text = file.read()
            document = Document()
            document.content = csv_text
            #print(f"CSVParser: Read {len(csv_text)} characters from {csv_text}")
            #return list(csv.DictReader(file))
            return document
