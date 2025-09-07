from loguru import logger

from rule_set.models.logical import (
    AndNode,
    LogicalNodeUnion,
    LogicalTree,
    NotNode,
    OrNode,
    RuleNode,
)

from ..errors import SerializerError, UnsupportedRuleTypeError
from .surge import serialize as surge_serialize

include_rule_types = [
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-WILDCARD",
    "DOMAIN-REGEX",
    "GEOSITE",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-SUFFIX",
    "IP-ASN",
    "GEOIP",
    "SRC-GEOIP",
    "SRC-IP-ASN",
    "SRC-IP-CIDR",
    "SRC-IP-SUFFIX",
    "DST-PORT",
    "SRC-PORT",
    "IN-PORT",
    "IN-TYPE",
    "IN-USER",
    "IN-NAME",
    "PROCESS-PATH",
    "PROCESS-PATH-REGEX",
    "PROCESS-NAME",
    "PROCESS-NAME-REGEX",
    "UID",
    "NETWORK",
    "DSCP",
    "RULE-SET",
    "PROTOCOL",
]
type_format = {"PROTOCOL": "NETWORK", "DEST-PORT": "DST-PORT"}


def _serialize_logical(*, node: LogicalNodeUnion) -> str:
    """Serialize logical node to string."""
    if isinstance(node, RuleNode):
        rule_type = type_format.get(node.rule.rule_type, node.rule.rule_type)
        if rule_type in include_rule_types:
            if rule_type == "NETWORK" and node.rule.rule_values[0].upper() not in [
                "UDP",
                "TCP",
            ]:
                raise UnsupportedRuleTypeError(node.rule.rule_type)
            return f"({rule_type},{','.join(node.rule.rule_values)}),"
        raise UnsupportedRuleTypeError(node.rule.rule_type)

    if isinstance(node, NotNode):
        rule = f"({node.operator},("
        rule += _serialize_logical(node=node.child)
        rule = rule.rstrip(",") + ")),"
        return rule

    elif isinstance(node, AndNode | OrNode):
        rule = f"({node.operator},("
        for child in node.get_children():
            rule += _serialize_logical(node=child)
        rule = rule.rstrip(",") + ")),"
        return rule


def serialize(*, tree: LogicalTree) -> str | None:
    """Serialize LogicalTree to string."""
    try:
        return _serialize_logical(node=tree.root)[1:-2]
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {surge_serialize(tree=tree)}, err: {e}")
    except SerializerError as e:
        logger.error(e)
