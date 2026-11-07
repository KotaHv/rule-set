from abc import ABC, abstractmethod
from datetime import UTC, datetime
from time import time

from rule_set.models import Artifact, Option, SerializableRuleModel


class BaseSerializer(ABC):
    def __init__(self, *, rules: SerializableRuleModel, option: Option) -> None:
        self.rules: SerializableRuleModel = rules
        self.option: Option = option
        self.last_updated_ts: float = time()
        self.last_updated: str = datetime.fromtimestamp(
            self.last_updated_ts, tz=UTC
        ).isoformat()

    @abstractmethod
    def serialize(self) -> list[Artifact]: ...
