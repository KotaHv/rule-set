import re
from abc import ABC, abstractmethod

from model import RuleModel


class BaseDeserialize(ABC):
    DEFAULT_EXCLUDE_KEYWORDS = [
        "th1s_rule5et_1s_m4d3_by_5ukk4w_ruleset.skk.moe",
        "this_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
        "this_rule_set_is_made_by_sukkaw.skk.moe",
        "acl4.ssr",
    ]

    COMMENT_PREFIXES = ["#", ";", "//"]

    def __init__(
        self,
        data: str | list[str],
        exclude_keywords: list[str] = [],
        exclude_suffixes: list[str] = [],
    ) -> None:
        if isinstance(data, str):
            data = data.splitlines()
        self.data_lines = data
        self.result = RuleModel()
        self.exclude_keywords = self.DEFAULT_EXCLUDE_KEYWORDS + exclude_keywords

        self.exclude_suffixes = exclude_suffixes
        self._compile_patterns()
        self.process()

    def _compile_patterns(self):
        if self.exclude_keywords:
            escaped_keywords = map(re.escape, self.exclude_keywords)
            self.exclude_keywords_pattern = re.compile(
                f"({'|'.join(escaped_keywords)})"
            )
        else:
            self.exclude_keywords_pattern = None

        if self.exclude_suffixes:
            escaped_suffixes = map(re.escape, self.exclude_suffixes)
            self.exclude_suffixes_pattern = re.compile(
                f"({'|'.join(escaped_suffixes)})$"
            )
        else:
            self.exclude_suffixes_pattern = None

        escaped_comments = map(re.escape, self.COMMENT_PREFIXES)
        comment_pattern = f"({'|'.join(escaped_comments)})"
        self.start_comment_pattern = re.compile(f"^({comment_pattern})")

        self.inline_comment_pattern = re.compile(comment_pattern)

    def process(self):
        processed_lines = []
        for line in self.data_lines:
            line = line.strip()
            if (
                not line
                or self.start_comment_pattern.search(line)
                or (
                    self.exclude_keywords_pattern
                    and self.exclude_keywords_pattern.search(line)
                )
                or (
                    self.exclude_suffixes_pattern
                    and self.exclude_suffixes_pattern.search(line)
                )
            ):
                continue
            line = self.inline_comment_pattern.split(line, maxsplit=1)[0].strip()
            processed_lines.append(line)
        self.data_lines = processed_lines

    @abstractmethod
    def deserialize(self) -> RuleModel: ...
