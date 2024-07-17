from abc import ABC, abstractmethod
from typing import List

from model import RuleModel

from .domain_set import DomainSetDeserialize
from .rule_set import RuleSetDeserialize

__all__ = [DomainSetDeserialize, RuleSetDeserialize]


class BaseDeserialize(ABC):
    def __init__(self, data: str | List[str]) -> None:
        if isinstance(data, str):
            data = data.splitlines()
        self.data_lines = data
        self.result = RuleModel()
        self.exclude_keywords = [
            "ruleset.skk.moe",
            "this_rule_set_is_made_by_sukkaw.skk.moe",
        ]
        self.process()

    def process(self):
        for i in range(len(self.data_lines) - 1, -1, -1):
            line = self.data_lines[i]
            line = line.strip()
            if (
                not line
                or line.startswith("#")
                or line.startswith("//")
                or any(keyword in line for keyword in self.exclude_keywords)
            ):
                del self.data_lines[i]
                continue
            for comment in ["#", "//"]:
                if comment in line:
                    self.data_lines[i] = line.split(comment)[0].strip()

    @abstractmethod
    def deserialize(self) -> RuleModel: ...
