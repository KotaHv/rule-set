import re
from abc import ABC, abstractmethod

from model import RuleModel

COMMENT_PATTERNS = ["#", ";", r"(?<!http:)(?<!https:)//"]
comment_pattern = f"({'|'.join(COMMENT_PATTERNS)})"
start_comment_pattern = re.compile(f"^({comment_pattern})")
inline_comment_pattern = re.compile(comment_pattern)


class BaseDeserialize(ABC):
    def __init__(
        self,
        data: str | list[str],
    ) -> None:
        if isinstance(data, str):
            data = data.splitlines()
        self.data_lines = data
        self.result = RuleModel()
        self.process()

    def process(self):
        processed_lines = []
        for line in self.data_lines:
            line = line.strip()
            if not line or start_comment_pattern.search(line):
                continue
            line = inline_comment_pattern.split(line, maxsplit=1)[0].strip()
            processed_lines.append(line)
        self.data_lines = processed_lines

    @abstractmethod
    def deserialize(self) -> RuleModel: ...
