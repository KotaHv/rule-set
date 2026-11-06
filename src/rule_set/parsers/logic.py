import re
import sys

from loguru import logger

from rule_set.errors import ParserError
from rule_set.models.logical import (
    ConcreteRule,
    Logical,
    LogicalOperator,
    LogicalTree,
    Node,
    Rule,
    RuleType,
)

parentheses_re = re.compile(r"^\((.*)\)$")


def split_outside_parentheses(s: str) -> list[str]:
    result: list[str] = []
    current: list[str] = []
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


def _parse_child(expression: str) -> Node:
    expression = remove_outer_parentheses(expression)
    parts = split_outside_parentheses(expression)
    if len(parts) < 2:
        raise ParserError(
            f"Invalid expression '{expression}': expected at least two comma-separated parts but found {len(parts)}"
        )
    if parts[0].upper() in LogicalOperator:
        operator = LogicalOperator(parts[0].upper())
        return _parse_logical_node(operator, parts[1])
    return _create_rule_node(parts[0], *parts[1:])


def _parse_logical_node(operator: LogicalOperator, expression: str) -> Logical:
    """Recursively parse logical expression into typed nodes."""
    expression = remove_outer_parentheses(expression)
    sub_expressions = split_outside_parentheses(expression)

    if operator is LogicalOperator.NOT:
        if len(sub_expressions) != 1:
            raise ParserError("NOT rule must only have one sub-rule")
        return Logical(
            op=LogicalOperator.NOT,
            children=(_parse_child(sub_expressions[0]),),
        )

    if len(sub_expressions) < 2:
        raise ParserError(
            f"Invalid {operator} rule: expected at least two sub-rules but found {len(sub_expressions)}.\nSub-rules:\n{', '.join(sub_expressions)}"
        )

    return Logical(
        op=operator,
        children=tuple(
            _parse_child(sub_expression) for sub_expression in sub_expressions
        ),
    )


def _create_rule_node(rule_type: str, *rule_values: str) -> Rule:
    """Create a rule node from type and values."""
    try:
        rule = ConcreteRule(rule_type=RuleType(rule_type), rule_values=rule_values)
        return Rule(rule=rule)
    except ValueError as e:
        raise ParserError(f"Invalid rule '{rule_type}': {e}") from None


def parse(rule: str) -> LogicalTree | None:
    """Parse logical rule string into LogicalTree."""
    try:
        rule = rule.replace(" ", "")
        parent_expression, sub_expression = split_outside_parentheses(rule)

        operator = LogicalOperator(parent_expression.upper())
        root = _parse_logical_node(operator, sub_expression)

        return LogicalTree(root=root)
    except (ParserError, ValueError) as e:
        logger.error(f"rule: '{rule}', err: {e}")
        return None


def render(
    node: Node,
    prefix: str = "",
    *,
    is_root: bool = True,
    is_last: bool = True,
) -> str:
    connector = "" if is_root else ("└── " if is_last else "├── ")
    if isinstance(node, Rule):
        rule = node.rule
        return (
            f"{prefix}{connector}"
            f"({rule.rule_type.value},{','.join(rule.rule_values)})\n"
        )

    result = f"{prefix}{connector}{node.op}\n"
    child_prefix = prefix + ("" if is_root else ("    " if is_last else "│   "))
    for index, child in enumerate(node.children):
        result += render(
            child,
            child_prefix,
            is_root=False,
            is_last=index == len(node.children) - 1,
        )
    return result


def print_rule_tree(rule: str | None = None):
    if rule is None:
        try:
            rule = sys.argv[1]
        except IndexError:
            rule = input("Please enter the logical rule: ")
    tree = parse(rule)
    if tree is None:
        return

    logger.success("\n" + render(tree.root))
