from dataclasses import dataclass,field

@dataclass
class Prompt:
    system_instruction: str
    context: str
    query: str