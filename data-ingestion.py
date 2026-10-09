import os
import sys
from packaging import metadata
import pandas as pd
import logging
from pathlib import Path
from abc import ABC, abstractmethod
logging.basicConfig(level=logging.INFO)


def parse_text_documents():
    p = Path('.')
    directorypathlist = [directorypathlist for directorypathlist in p.iterdir() if directorypathlist.is_dir()]
    print (directorypathlist)
    files_contents_dict = {}
    metadata_dict = {}
    for directoryPath in directorypathlist:
        for file_path in directoryPath.rglob("*"):
            if file_path.is_file():
               with open(file_path, 'rb') as file:
                    metadata = file_path.stat()
                    print('file_path', file_path,metadata)
                    data = file.read()
                    files_contents_dict[file_path] = data.decode('cp1252', errors='ignore')  


    #print(files_contents_dict)
    '''for file_path, content in files_contents_dict.items():
        print(f"File: {file_path}")
        print(f"Content: {content[:10000]}...")  # Print first 100 characters of content
        print("-" * 40)
        break'''
      
    pass

def parse_csv_files():
    pass

