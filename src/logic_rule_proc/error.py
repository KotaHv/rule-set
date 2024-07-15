class UnsupportedRuleTypeError(Exception):
    def __init__(self, rule_type: str):
        super().__init__(f"Unsupported rule type: {rule_type}")


class DeserializeError(Exception): ...
