from dataclasses import dataclass,field
from datetime import datetime
from pathlib import Path
from datetime import datetime, timezone
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from docx.text.paragraph import Paragraph
import uuid

@dataclass
class FileMetadata:
    file_id: str
    file_name: str
    file_path: str
    file_extension: str
    file_permissions: int
    file_owner: int 
    document_id:str 
    file_last_accessed: datetime
    file_last_modified: datetime
    file_creation_time: datetime
    size: int

    @classmethod
    def from_path(cls, file_path: Path) -> 'FileMetadata':
        metadata = file_path.stat()
        return cls(
            file_id=str(metadata.st_ino),
            file_name=file_path.name,
            file_path=str(file_path.resolve()),
            file_extension=file_path.suffix.lower(),
            file_permissions=metadata.st_mode,
            file_owner=metadata.st_uid,
            document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, str(file_path.resolve()))),
            file_last_accessed=datetime.fromtimestamp(metadata.st_atime),# tz=timezone.utc),
            file_last_modified=datetime.fromtimestamp(metadata.st_mtime),# tz=timezone.utc),
            file_creation_time=datetime.fromtimestamp(metadata.st_ctime),# tz=timezone.utc),
            size=metadata.st_size
        )       
@dataclass
class Table:
    sheet:str = "" #excel sheet number containing the table
    range:str = "" #cell range of the table
    headers = [] #excel tables header e.g. ["Category", "Target_Goal"]
    '''
    an array of dictionaries. Each dictionary contains  {
                            "sheet": sheet_name,
                            "type": "Implicit Region",
                            "name": f"Implicit_{range_str}",
                            "range": range_str,
                            "dataframe": df,
                        }
    '''
    data = []

@dataclass
class Document:
    content: str = ''
    metadata: FileMetadata | None = None
    tables_list:list[Table] = field (default_factory=list)
    paragraph_list: list[Paragraph] = field(default_factory=list)

@dataclass
class ParagraphPiece:
    content: str = ""

    source_paragraph: int = 0
    start: int = 0
    end: int = 0
    
    contains_residual_text:bool = False

    overlap_start: int | None = None
    overlap_end: int | None = None

    residual_start: int | None = None
    residual_end: int | None = None

    meta_data: dict[str, object] = field(default_factory=dict)