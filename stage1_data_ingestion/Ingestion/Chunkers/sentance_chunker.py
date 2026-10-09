from stage1_data_ingestion.Ingestion.Chunkers.chunker import Chunker
from stage1_data_ingestion.Ingestion.Chunkers.chunk import Chunk
from stage1_data_ingestion.Ingestion.models import Document
#return [sentence.strip() for sentence in sentences if sentence.strip()]


class SentanceChunker(Chunker):
    """Chunker for plain-text documents."""
    def __init__(self, chunk1: Chunk):
        self.chunk1 = chunk1

    def chunk(self, document: Document):
        sentences = document.content.split('.')
        # print('sentances: ',sentences)
        index = 0
        
        sentance_list = []
        chunk_list = []
        for sentance in sentences:
             if sentance.strip():
                sentance_list.append(sentance.strip())
        for i in sentance_list:
                    chk_id = Chunker.chunk_Id()
                    chk1 = Chunk()
                    chk1.chunk_id = chk_id
                    chk1.document_id = document.metadata.file_id
                    chk1.chunk_index = index
                    chk1.content = i
                    #print (f'at index: {index}  chunk contents:{i}')
                    chk1.metadata['filename'] = document.metadata.file_name
                    chk1.metadata['extension'] = document.metadata.file_extension
                    chk1.metadata['owner'] = document.metadata.file_owner
                    chunk_list.append(chk1)
                    #print(f'chunk meta data: {chk1.metadata}')
					#print (f'index: {index} chunk_id: {chk_id})# sentance len:{len(sentences)}')
                    index += 1
        #print (f'chunlist: {chunk_list}')
        return chunk_list
    