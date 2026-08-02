from ..models import BaseResource


class RuleSetError(Exception):
    pass


class ParserError(RuleSetError):
    pass


class SerializerError(RuleSetError):
    pass


class UnsupportedRuleTypeError(SerializerError):
    def __init__(self, rule_type: str):
        self.rule_type = rule_type
        super().__init__(f"Unsupported rule type: {rule_type}")


class FetchError(RuleSetError):
    pass


class ResourceError(RuleSetError):
    pass


class UnknownResourceTypeError(ResourceError):
    def __init__(self, resource: BaseResource):
        self.resource_type = resource
        super().__init__(f"Unknown resource type: {type(resource)}")


__all__ = [
    "FetchError",
    "ParserError",
    "ResourceError",
    "RuleSetError",
    "SerializerError",
    "UnknownResourceTypeError",
    "UnsupportedRuleTypeError",
]
