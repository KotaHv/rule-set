from loguru import logger

from rule_set.errors import SerializerError, UnsupportedRuleTypeError
from rule_set.models.logical import (
    Logical,
    LogicalOperator,
    LogicalTree,
    Node,
    Rule,
)

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


def _serialize_logical(*, node: Node) -> str:
    """Serialize logical node to string."""
    match node:
        case Rule(rule=rule):
            rule_type = type_format.get(rule.rule_type, rule.rule_type)
            if rule_type in include_rule_types:
                if rule_type == "NETWORK" and rule.rule_values[0].upper() not in [
                    "UDP",
                    "TCP",
                ]:
                    raise UnsupportedRuleTypeError(rule.rule_type)
                return f"({rule_type},{','.join(rule.rule_values)}),"
            raise UnsupportedRuleTypeError(rule.rule_type)

        case Logical(op=LogicalOperator.NOT, children=(child,)):
            inner = _serialize_logical(node=child)
            return f"({node.op},({inner.rstrip(',')})),"

        case Logical(op=op, children=children):
            inner = "".join(_serialize_logical(node=child) for child in children)
            return f"({op},({inner.rstrip(',')})),"


def serialize(*, tree: LogicalTree) -> str | None:
    """Serialize LogicalTree to string."""
    try:
        return _serialize_logical(node=tree.root)[1:-2]
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {surge_serialize(tree=tree)}, err: {e}")
    except SerializerError as e:
        logger.error(e)
