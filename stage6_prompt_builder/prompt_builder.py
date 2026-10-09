from stage6_prompt_builder.prompt_models import Prompt

class PromptBuilder:
    def __init__(self,instructions: str):
        self.instructions = instructions

    def set_instructions(self, instructions:str):
        self.instructions = instructions

    def get_instructions(self):
        return self.instructions

    def build_prompt(self, question: str, context: str) -> str:
        return f"Instructions:\n{self.instructions}\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{query}"

    
