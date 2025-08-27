import re
from abc import ABC, abstractmethod

from model import RuleModel


class BaseDeserialize(ABC):
    COMMENT_PREFIXES = ["#", ";", "//"]

    def __init__(
        self,
        data: str | list[str],
    ) -> None:
        if isinstance(data, str):
            data = data.splitlines()
        self.data_lines = data
        self.result = RuleModel()
        self._compile_patterns()
        self.process()

    def _compile_patterns(self):
        escaped_comments = map(re.escape, self.COMMENT_PREFIXES)
        comment_pattern = f"({'|'.join(escaped_comments)})"
        self.start_comment_pattern = re.compile(f"^({comment_pattern})")

        self.inline_comment_pattern = re.compile(comment_pattern)

    def process(self):
        processed_lines = []
        for line in self.data_lines:
            line = line.strip()
            if not line or self.start_comment_pattern.search(line):
                continue
            line = self.inline_comment_pattern.split(line, maxsplit=1)[0].strip()
            processed_lines.append(line)
        self.data_lines = processed_lines

    @abstractmethod
    def deserialize(self) -> RuleModel: ...
