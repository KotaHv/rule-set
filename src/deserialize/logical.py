import re
import sys
from typing import List

from anytree import Node, RenderTree
from loguru import logger

from .error import DeserializeError
from utils import is_logical_keyword, is_logical_and_or, is_logical_not

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


def _deserialize(parent: Node, expression: str):
    expression = remove_outer_parentheses(expression)
    sub_expressions = split_outside_parentheses(expression)
    if not is_logical_keyword(parent.name):
        raise DeserializeError(
            f"{parent.name} is not a valid logical operator. Valid operators are: AND, OR, NOT"
        )
    if is_logical_not(parent.name) and len(sub_expressions) != 1:
        raise DeserializeError("NOT rule must only have one sub-rule")
    elif is_logical_and_or(parent.name) and len(sub_expressions) < 2:
        raise DeserializeError("AND/OR rule must have at least two sub-rules")
    for sub_expression in sub_expressions:
        sub_expression = remove_outer_parentheses(sub_expression)
        sub_parts = split_outside_parentheses(sub_expression)
        parent_expression = sub_parts[0].upper()
        if is_logical_keyword(parent_expression):
            sub_node = Node(parent_expression, parent=parent)
            _deserialize(sub_node, sub_parts[1])
        else:
            if len(sub_parts) < 2:
                raise DeserializeError(f"Format error of '{expression}': {sub_parts}")
            Node(tuple(sub_parts), parent=parent)


def deserialize(rule: str) -> Node | None:
    try:
        rule = rule.replace(" ", "")
        parent_expression, sub_expression = split_outside_parentheses(rule)
        parent_node = Node(parent_expression.upper())
        _deserialize(parent_node, sub_expression)
        return parent_node
    except DeserializeError as e:
        logger.error(f"rule: '{rule}', err: {e}")


def print_rule_tree(rule: str | None = None):
    if rule is None:
        try:
            rule = sys.argv[1]
        except IndexError:
            rule = input("Please enter the logical rule: ")
    node = deserialize(rule)
    if node is None:
        return
    for pre, _, node in RenderTree(node):
        logger.success(f"{pre}{node.name}")
