from sentence_transformers import SentenceTransformer
from stage2_embedding.embedding_model import EmbeddedChunk
class EmbeddingGenerator:

    def __init__(self,
        model_name,
        device=None,
        batch_size=32):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.model = SentenceTransformer(
            model_name
        )
        self.embedding_dimension = (self.model.get_sentence_embedding_dimension()) 

    def generate_embedding(self, text):
        embedding = self.model.encode(text,batch_size=self.batch_size)
        #print(embedding)
        return embedding

    def generate_embeddings(self, chunks):
        texts = [chunk.content for chunk in chunks]
        embeddings = self.model.encode(texts,batch_size=self.batch_size)
        embed_chunks = []
        for chunk, embedding in zip(chunks,embeddings):            
            embed_chunk = EmbeddedChunk()
            embed_chunk.chunk = chunk
            embed_chunk.embedding = embedding
            embed_chunks.append(embed_chunk)
        return embed_chunks

    def get_embedding_dimension(self):
        return self.embedding_dimension