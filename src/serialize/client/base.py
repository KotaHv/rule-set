from abc import ABC, abstractmethod

from model import SerializableRuleModel, Option


class BaseSerialize(ABC):
    def __init__(self, *, rules: SerializableRuleModel, option: Option) -> None:
        self.rules = rules
        self.option = option

    @abstractmethod
    def serialize(self) -> str: ...
