import re
from typing import List

from loguru import logger

import logic_rule_proc
from model import RuleModel

parentheses_re = re.compile(r"^\((.*)\)$")


def split_outside_parentheses(s: str) -> List[str]:
    result = []
    current = []
    level = 0

    for char in s:
        if char == "," and level == 0:
            result.append("".join(current))
            current = []
        else:
            if char == "(":
                level += 1
            elif char == ")":
                level -= 1
            current.append(char)

    result.append("".join(current))
    return result


def remove_outer_parentheses(text: str) -> str:
    match = parentheses_re.match(text)
    if match:
        return match.group(1)
    return text


class Parser:
    def __init__(self, data: str) -> None:
        self.result = RuleModel()
        self.data_lines = data.splitlines()
        self.logical = ["and", "or", "not"]
        self.exclude_keywords = [
            "ruleset.skk.moe",
            "this_rule_set_is_made_by_sukkaw.skk.moe",
        ]

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
            for comment in ["#", "//"]:
                if comment in line:
                    self.data_lines[i] = line.split(comment)[0].strip()

    def parse_domain_set(self):
        for hostname in self.data_lines:
            if hostname.startswith("."):
                self.result.domain_suffix.add(hostname.lstrip("."))
            else:
                self.result.domain.add(hostname)

    def parse_rule_set(self):
        unique_node_list = []
        for line in self.data_lines:
            processed_line = line.split(",")
            rule_type, rule = processed_line[0].lower(), processed_line[1].strip()
            if rule_type == "domain":
                self.result.domain.add(rule)
            elif rule_type == "domain-suffix":
                self.result.domain_suffix.add(rule)
            elif rule_type == "domain-keyword":
                self.result.domain_keyword.add(rule)
            elif rule_type == "domain-wildcard":
                self.result.domain_wildcard.add(rule)
            elif rule_type == "ip-cidr":
                self.result.ip_cidr.add(rule)
            elif rule_type == "ip-cidr6":
                self.result.ip_cidr6.add(rule)
            elif rule_type == "ip-asn":
                self.result.ip_asn.add(rule)
            elif rule_type == "user-agent":
                self.result.ua.add(rule)
            elif rule_type == "process-name":
                self.result.process.add(rule)
            elif rule_type in self.logical:
                node = logic_rule_proc.deserialize(line)
                if node is None:
                    continue
                if line not in unique_node_list:
                    unique_node_list.append(line)
                    self.result.logical.append(node)
            else:
                logger.warning(line)

    def parse(self):
        self.process()
        line = self.data_lines[0]
        processed_line = line.split(",")
        if len(processed_line) == 1:
            self.parse_domain_set()
        else:
            self.parse_rule_set()
