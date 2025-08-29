from anytree import Node
from loguru import logger

from ..error import UnsupportedRuleTypeError, SerializeError
from .surge import serialize as surge_serialize
from utils import is_logical_keyword, is_logical_not, is_logical_and_or

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


def _serialize(*, node: Node) -> str:
    if isinstance(node.name, tuple):
        rule_type = type_format.get(node.name[0].upper(), node.name[0].upper())
        if rule_type in include_rule_types:
            if rule_type == "NETWORK" and node.name[1].upper() not in ["UDP", "TCP"]:
                raise UnsupportedRuleTypeError(node.name[0])
            return f"({','.join([rule_type, *node.name[1:]])}),"
        raise UnsupportedRuleTypeError(node.name[0])
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
        rule += _serialize(node=child)
    rule = rule.rstrip(",") + ")),"
    return rule


def serialize(*, root_node: Node) -> str | None:
    try:
        return _serialize(node=root_node)[1:-2]
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {surge_serialize(root_node=root_node)}, err: {e}")
    except SerializeError as e:
        logger.error(e)
