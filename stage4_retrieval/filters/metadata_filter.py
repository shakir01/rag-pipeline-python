from stage4_retrieval.models.filter_condition import FilterCondition

class MetadataFilter:
    def __init__(self, filter_conditions: list[FilterCondition]=None):
        self.filter_conditions = filter_conditions or []

    def set_conditions(self, filter_conditions):
        self.filter_conditions = filter_conditions

    def matches(self, item_metadata: dict) -> bool:
        for condition in self.filter_conditions:
            #actual_value = item_metadata.get(condition.field)
            actual_value = getattr(item_metadata, condition.field, None)
            if actual_value is None:
                return False
            
            operator = condition.operator
            target_value = condition.value
            
            if operator == "equals":
                if actual_value != target_value:
                    return False
            elif operator == "in":
                if not isinstance(target_value, (list, tuple, set)):
                    raise TypeError(
                        "'in' operator requires a list, tuple, or set as value."
                    )
                if actual_value not in target_value:
                    return False
            elif operator == "contains":
                if str(target_value).lower() not in str(actual_value).lower():
                    return False
            else:
                return False
                
        return True