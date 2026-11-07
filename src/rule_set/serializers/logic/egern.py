from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from loguru import logger

from rule_set.errors import SerializerError, UnsupportedRuleTypeError
from rule_set.models.logical import (
    Logical,
    LogicalOperator,
    LogicalTree,
    Node,
    Rule,
    RuleType,
)

from .surge import serialize as surge_serialize

type LogicalSetName = Literal["and_set", "or_set", "not_set"]


@dataclass(frozen=True)
class TaggedMapping:
    tag: str
    match: str | TaggedMapping | list[TaggedMapping]
    no_resolve: bool = False


include_type = [
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-WILDCARD",
    "DOMAIN-KEYWORD",
    "DOMAIN-REGEX",
    "GEOIP",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-ASN",
    "URL-REGEX",
    "USER-AGENT",
    "SSID",
    "BSSID",
    "PROTOCOL",
    "DEST-PORT",
]
type_format = {
    "DOMAIN": "domain",
    "DOMAIN-SUFFIX": "domain_suffix",
    "DOMAIN-WILDCARD": "domain_wildcard",
    "DOMAIN-KEYWORD": "domain_keyword",
    "DOMAIN-REGEX": "domain_regex",
    "GEOIP": "geoip",
    "IP-CIDR": "ip_cidr",
    "IP-CIDR6": "ip_cidr",
    "IP-ASN": "asn",
    "URL-REGEX": "url_regex",
    "USER-AGENT": "user_agent",
    "SSID": "ssid",
    "BSSID": "bssid",
    "PROTOCOL": "protocol",
    "DEST-PORT": "dest_port",
}


def _serialize_logical(*, node: Node) -> TaggedMapping:
    match node:
        case Rule(rule=rule):
            return format_rule(rule.rule_type, rule.rule_values)

        case Logical(op=LogicalOperator.NOT, children=(child,)):
            return TaggedMapping("!not", _serialize_logical(node=child))

        case Logical(op=op, children=children):
            return TaggedMapping(
                f"!{op.lower()}",
                [_serialize_logical(node=child) for child in children],
            )


def serialize(
    *, tree: LogicalTree
) -> tuple[LogicalSetName, list[TaggedMapping] | TaggedMapping] | None:
    try:
        match tree.root:
            case Logical(op=LogicalOperator.NOT, children=(child,)):
                return "not_set", _serialize_logical(node=child)
            case Logical(op=LogicalOperator.AND, children=children):
                return "and_set", [_serialize_logical(node=child) for child in children]
            case Logical(op=LogicalOperator.OR, children=children):
                return "or_set", [_serialize_logical(node=child) for child in children]
            case _:
                return None
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {surge_serialize(tree=tree)}, err: {e}")
    except SerializerError as e:
        logger.error(e)


def format_rule(rule_type: RuleType, rule_values: Sequence[str]) -> TaggedMapping:
    rule_type_name = rule_type.upper()
    if rule_type_name not in include_type:
        raise UnsupportedRuleTypeError(rule_type_name)
    no_resolve = any(value.lower() == "no-resolve" for value in rule_values[1:])
    return TaggedMapping(f"!{type_format[rule_type_name]}", rule_values[0], no_resolve)
