from abc import ABC,abstractmethod

class LLMGenerator:
    def __init__(self):
        pass

    @abstractmethod
    def generate (self,prompt:str):
        return ''
