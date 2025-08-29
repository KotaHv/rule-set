from loguru import logger

from ..error import UnsupportedRuleTypeError, SerializeError
from model.logical import (
    LogicalTree,
    AndNode,
    OrNode,
    NotNode,
    RuleNode,
    LogicalNodeUnion,
)


def _serialize_logical(
    *, node: LogicalNodeUnion, include: list[str] | None = None
) -> str:
    """Serialize logical node to string."""
    if isinstance(node, RuleNode):
        rule_type = node.rule.rule_type
        if include is not None and rule_type.upper() not in include:
            raise UnsupportedRuleTypeError(rule_type)
        return f"({rule_type},{','.join(node.rule.rule_values)}),"

    if isinstance(node, NotNode):
        rule = f"({node.operator},("
        rule += _serialize_logical(node=node.child, include=include)
        rule = rule.rstrip(",") + ")),"
        return rule

    elif isinstance(node, (AndNode, OrNode)):
        rule = f"({node.operator},("
        for child in node.get_children():
            rule += _serialize_logical(node=child, include=include)
        rule = rule.rstrip(",") + ")),"
        return rule


def serialize(*, tree: LogicalTree, include: list[str] | None = None) -> str | None:
    """Serialize LogicalTree to string."""
    try:
        return _serialize_logical(node=tree.root, include=include)[1:-2]
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {serialize(tree=tree)}, err: {e}")
    except SerializeError as e:
        logger.error(e)
