from stage1_data_ingestion.Ingestion.Chunkers.chunker import Chunker
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk
from stage1_data_ingestion.Ingestion.models import Document
from stage1_data_ingestion.Ingestion.Chunkers import chunk
from openpyxl.utils.cell import range_boundaries
from scipy.ndimage import label
from tokenize import group
from typing import Any
import pandas as pd
import openpyxl
import json

class SpreadSheetChunker(Chunker):
    def __init__(self,document:Document):
        pass

    def create_chunk(self,index, document:Document, lst:list,item):
        chnk:Chunk = Chunk()
        chnk.chunk_id = Chunker.chunk_Id()
        chnk.chunk_index = index
        chnk.content = json.dumps(lst)
        chnk.metadata['filename'] = document.metadata.file_name
        chnk.metadata['extension'] = document.metadata.file_extension
        chnk.metadata['owner'] = document.metadata.file_owner
        chnk.metadata['sheet'] = item['sheet']
        chnk.metadata['type'] = item ['type']
        chnk.metadata['name'] = item ['name']
        chnk.metadata['range'] = item['range']
        headers = (item['dataframe']).columns
        chnk.metadata['headers'] = json.dumps(list(headers))
        #print(f'Chunk: {chnk}')
        return chnk
    
    def chunk(self,document:Document):
        #for item in document.tables_list:
        #   headers = (item['dataframe']).columns
        #    #print(f'Table Headers: {headers}')
        chunk_list = []
        chnk_index = 0
        for  item in document.tables_list:
            df = item['dataframe']
            row_records = df.to_dict(orient="records")
            #print(f'Data Frame: {row_records} data frame size: {len(df)}')
            group_size = 3
            groupList = []
            chunk_list = []
            chnk_index = 0
            index = 0

            for row in row_records:
                #groupList.append(json.dumps(row));
                groupList.append(row)
                if (index + 1) % group_size == 0:
                    chnk = self.create_chunk(chnk_index,document,groupList,item)
                    
                    chunk_list.append(chnk)
                    chnk_index += 1
                index += 1

            if len(groupList) > 0:
                chunk_list.append(self.create_chunk(chnk_index, document, groupList,item))
                chnk_index += 1

            #print('chunk_list: ',chunk_list)
            '''for row in row_records:
                json_str = json.dumps(row)
                #print(f'row: {row} -----> row type: {type(row)}')
                print(f'json string: {json_str} type:{type(json_str)} number of rows:{len(row_records)} document.tables_list:{len(document.tables_list)}')
            print('////////////////////////////////////////////')'''
            
            '''for headers,series in item['dataframe'].items():
                print(f'headers: {headers} values: {series.tolist()} number of items:{len(series)}')
                chnker:Chunk = Chunk()
                chnker.chunk_id = Chunker.chunk_Id()
                chnker.chunk_index
            print('\n///////////////////////////////////////////////')'''
        return chunk_list