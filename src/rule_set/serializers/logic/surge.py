from loguru import logger

from rule_set.errors import SerializerError, UnsupportedRuleTypeError
from rule_set.models.logical import (
    Logical,
    LogicalOperator,
    LogicalTree,
    Node,
    Rule,
)


def _serialize_logical(*, node: Node, include: list[str] | None = None) -> str:
    """Serialize logical node to string."""
    match node:
        case Rule(rule=rule):
            rule_type = rule.rule_type
            if include is not None and rule_type.upper() not in include:
                raise UnsupportedRuleTypeError(rule_type)
            return f"({rule_type},{','.join(rule.rule_values)}),"

        case Logical(op=LogicalOperator.NOT, children=(child,)):
            inner = _serialize_logical(node=child, include=include)
            return f"({node.op},({inner.rstrip(',')})),"

        case Logical(op=op, children=children):
            inner = "".join(
                _serialize_logical(node=child, include=include) for child in children
            )
            return f"({op},({inner.rstrip(',')})),"


def _serialize_tree(*, tree: LogicalTree, include: list[str] | None = None) -> str:
    return _serialize_logical(node=tree.root, include=include)[1:-2]


def serialize(*, tree: LogicalTree, include: list[str] | None = None) -> str | None:
    """Serialize LogicalTree to string."""
    try:
        return _serialize_tree(tree=tree, include=include)
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {_serialize_tree(tree=tree)}, err: {e}")
    except SerializerError as e:
        logger.error(e)
