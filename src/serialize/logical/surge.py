from typing import List

from anytree import Node
from loguru import logger

from serialize.error import UnsupportedRuleTypeError, SerializeError
from utils import is_logical_keyword, is_logical_not, is_logical_and_or


def _serialize(*, node: Node, include: List[str] | None = None) -> str:
    if isinstance(node.name, tuple):
        if include is not None and node.name[0].upper() not in include:
            raise UnsupportedRuleTypeError(node.name[0])
        return f"({",".join(node.name)}),"
    if not is_logical_keyword(node.name):
        raise SerializeError(
            f"{node.name} is not a valid logical operator. Valid operators are: AND, OR, NOT",
            node=node.root,
        )
    if is_logical_not(node.name) and len(node.children) != 1:
        raise SerializeError(
            "NOT rule must only have one sub-rule",
            node=node.root,
        )
    elif is_logical_and_or(node.name) and len(node.children) < 2:
        raise SerializeError(
            "AND/OR rule must have at least two sub-rules",
            node=node.root,
        )
    rule = f"({node.name},("
    for child in node.children:
        rule += _serialize(node=child, include=include)
    rule = rule.rstrip(",") + ")),"
    return rule


def serialize(*, root_node: Node, include: List[str] | None = None) -> str | None:
    try:
        return _serialize(node=root_node, include=include)[1:-2]
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {_serialize(node=root_node)}, err: {e}")
    except SerializeError as e:
        logger.error(e)
