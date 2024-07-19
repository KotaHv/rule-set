from abc import ABC, abstractmethod

from model import RuleModel, SerializeOption


class BaseSerialize(ABC):
    def __init__(self, *, rules: RuleModel, option: SerializeOption) -> None:
        self.rules = rules
        self.option = option

    @abstractmethod
    def serialize(self) -> str: ...
