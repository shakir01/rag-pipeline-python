from dataclasses import dataclass,field

@dataclass
class FilterCondition:
    field: str
    operator: str
    value: object