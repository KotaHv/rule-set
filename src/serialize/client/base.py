from abc import ABC, abstractmethod

from model import RuleModel, Option


class BaseSerialize(ABC):
    def __init__(self, *, rules: RuleModel, option: Option) -> None:
        self.rules = rules
        self.option = option

    @abstractmethod
    def serialize(self) -> str: ...
