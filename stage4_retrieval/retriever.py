from abc import ABC,abstractmethod
from stage4_retrieval.models.retrieval_request import RetrievalRequest
class Retriever (ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def retrieve(self, retrieval_request: RetrievalRequest):
        pass