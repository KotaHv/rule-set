from abc import ABC, abstractmethod

from rule_set.models import Option, SerializableRuleModel


class BaseSerializer[In, Out](ABC):
    @abstractmethod
    def serialize(self, value: In, /) -> Out: ...


class BaseRuleSerializer[Out](BaseSerializer[SerializableRuleModel, Out], ABC):
    def __init__(self, *, option: Option, last_updated: str) -> None:
        self.option: Option = option
        self.last_updated: str = last_updated
