from abc import ABC, abstractmethod

from rule_set.models import Option, SerializableRuleModel


class BaseSerializer(ABC):
    def __init__(self, *, rules: SerializableRuleModel, option: Option) -> None:
        self.rules = rules
        self.option = option

    @abstractmethod
    def serialize(self) -> str | bytes | None: ...
