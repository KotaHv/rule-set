import re
import sys

from loguru import logger

from .error import DeserializeError
from model.logical import (
    LogicalTree,
    AndNode,
    OrNode,
    NotNode,
    RuleNode,
    ConcreteRule,
    RuleType,
    LogicalOperator,
)

parentheses_re = re.compile(r"^\((.*)\)$")


def split_outside_parentheses(s: str) -> list[str]:
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


def _deserialize_logical_node(
    operator: LogicalOperator, expression: str
) -> AndNode | OrNode | NotNode | RuleNode:
    """Recursively deserialize logical expression into typed nodes."""
    expression = remove_outer_parentheses(expression)
    sub_expressions = split_outside_parentheses(expression)

    if operator == LogicalOperator.NOT:
        if len(sub_expressions) != 1:
            raise DeserializeError("NOT rule must only have one sub-rule")

        sub_expression = sub_expressions[0]
        sub_expression = remove_outer_parentheses(sub_expression)
        sub_parts = split_outside_parentheses(sub_expression)

        if sub_parts[0].upper() in LogicalOperator:
            # Nested operator
            sub_operator = LogicalOperator(sub_parts[0].upper())
            child = _deserialize_logical_node(sub_operator, sub_parts[1])
        else:
            # Concrete rule
            if len(sub_parts) < 2:
                raise DeserializeError(f"Invalid rule format: {sub_expression}")
            child = _create_rule_node(sub_parts[0], *sub_parts[1:])

        return NotNode(child=child)

    elif operator in (LogicalOperator.AND, LogicalOperator.OR):
        if len(sub_expressions) < 2:
            raise DeserializeError(
                f"Invalid {operator} rule: expected at least two sub-rules but found {len(sub_expressions)}.\n"
                f"Sub-rules:\n"
                f"{', '.join(sub_expressions)}"
            )

        children = []
        for sub_expression in sub_expressions:
            sub_expression = remove_outer_parentheses(sub_expression)
            sub_parts = split_outside_parentheses(sub_expression)
            if sub_parts[0].upper() in LogicalOperator:
                # Nested operator
                sub_operator = LogicalOperator(sub_parts[0].upper())
                child = _deserialize_logical_node(sub_operator, sub_parts[1])
            else:
                # Concrete rule
                if len(sub_parts) < 2:
                    raise DeserializeError(f"Invalid rule format: {sub_expression}")
                child = _create_rule_node(sub_parts[0], *sub_parts[1:])

            children.append(child)

        if operator == LogicalOperator.AND:
            return AndNode(children=children)
        else:
            return OrNode(children=children)


def _create_rule_node(rule_type: str, *rule_values: str) -> RuleNode:
    """Create a rule node from type and values."""
    try:
        rule = ConcreteRule(
            rule_type=RuleType(rule_type), rule_values=list(rule_values)
        )
        return RuleNode(rule=rule)
    except ValueError as e:
        raise DeserializeError(f"Invalid rule type '{rule_type}': {e}")


def deserialize(rule: str) -> LogicalTree | None:
    """Deserialize logical rule string into LogicalTree."""
    try:
        rule = rule.replace(" ", "")
        parent_expression, sub_expression = split_outside_parentheses(rule)

        # Create root node based on operator
        operator = LogicalOperator(parent_expression.upper())
        root = _deserialize_logical_node(operator, sub_expression)

        return LogicalTree(root=root)
    except DeserializeError as e:
        logger.error(f"rule: '{rule}', err: {e}")
        return None
    except ValueError as e:
        logger.error(f"rule: '{rule}', err: {e}")
        return None


def print_rule_tree(rule: str | None = None):
    if rule is None:
        try:
            rule = sys.argv[1]
        except IndexError:
            rule = input("Please enter the logical rule: ")
    tree = deserialize(rule)
    if tree is None:
        return

    logger.success("\n" + tree.render())
