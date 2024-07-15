import re
import sys
from typing import List

from loguru import logger
from anytree import Node, RenderTree

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
            if (
                not line
                or line.startswith("#")
                or any(keyword in line for keyword in self.exclude_keywords)
            ):
                del self.data_lines[i]

    def parse_domain_set(self):
        for hostname in self.data_lines:
            if hostname.startswith("."):
                self.result.domain_suffix.add(hostname.lstrip("."))
            else:
                self.result.domain.add(hostname)

    def parse_rule_set(self):
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
                self.result.logical.add(line)
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

    @staticmethod
    def build_logical_tree_from_expression(parent_node: Node, logical_expression: str):
        logical_expression = remove_outer_parentheses(logical_expression)
        sub_expressions = split_outside_parentheses(logical_expression)
        for sub in sub_expressions:
            sub = remove_outer_parentheses(sub)
            sub_parts = split_outside_parentheses(sub)
            parent_str = sub_parts[0] = sub_parts[0].upper()
            if parent_str not in ["AND", "OR", "NOT"]:
                Node(tuple(sub_parts), parent=parent_node)
            else:
                sub_node = Node(parent_str, parent=parent_node)
                Parser.build_logical_tree_from_expression(sub_node, sub_parts[1])

    @staticmethod
    def parse_logical_rule(logical_rule: str) -> Node:
        logical_rule = logical_rule.replace(" ", "")
        parent_str, sub_str = split_outside_parentheses(logical_rule)
        parent_node = Node(parent_str.upper())
        Parser.build_logical_tree_from_expression(parent_node, sub_str)
        return parent_node

    @staticmethod
    def print_logical_rule_tree(logical_rule: str | None = None):
        if logical_rule is None:
            try:
                logical_rule = sys.argv[1]
            except IndexError:
                logical_rule = input("Please enter the logical rule: ")
        node = Parser.parse_logical_rule(logical_rule)
        for pre, _, node in RenderTree(node):
            print(f"{pre}{node.name}")


if __name__ == "__main__":
    from anytree import RenderTree

    rule = """AND,(
    (OR,(
        (AND,(
            (NOT,(
                (OR,(
                    (DEST-PORT,6095), 
                    (DEST-PORT,80), 
                    (DEST-PORT,443)
                ))
            )), 
            (DEST-PORT,1-65535)
        )), 
        (DOMAIN,milink.pandora.xiaomi.com,extended-matching), 
        (DOMAIN-SUFFIX,cibntv.net,extended-matching)
    )), 
    (SRC-IP,10.0.1.7)
)""".replace("\n", "")
    print(rule)

    node = Parser.parse_logical_rule(rule)
    for pre, _, node in RenderTree(node):
        print("%s%s" % (pre, node.name))
