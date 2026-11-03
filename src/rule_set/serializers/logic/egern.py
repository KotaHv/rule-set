from dataclasses import dataclass

from loguru import logger

from rule_set.errors import SerializerError, UnsupportedRuleTypeError
from rule_set.models.logical import (
    AndNode,
    LogicalNodeUnion,
    LogicalTree,
    NotNode,
    OrNode,
    RuleNode,
)

from .surge import serialize as surge_serialize


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


def _serialize_logical(*, node: LogicalNodeUnion) -> TaggedMapping:
    if isinstance(node, RuleNode):
        return format_rule(node.rule.rule_type, node.rule.rule_values)

    if isinstance(node, NotNode):
        return TaggedMapping("!not", _serialize_logical(node=node.child))

    logical_type = f"!{node.operator.lower()}"
    return TaggedMapping(
        logical_type, [_serialize_logical(node=child) for child in node.get_children()]
    )


def serialize(
    *, tree: LogicalTree
) -> tuple[str, list[TaggedMapping] | TaggedMapping] | None:
    try:
        logical_type = tree.root.operator.lower()
        logical_set = f"{logical_type}_set"
        if isinstance(tree.root, AndNode | OrNode):
            return logical_set, [
                _serialize_logical(node=child) for child in tree.root.get_children()
            ]
        return logical_set, _serialize_logical(node=tree.root.child)
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {surge_serialize(tree=tree)}, err: {e}")
    except SerializerError as e:
        logger.error(e)


def format_rule(rule_type: str, rule_values: list[str]) -> TaggedMapping:
    rule_type = rule_type.upper()
    if rule_type not in include_type:
        raise UnsupportedRuleTypeError(rule_type)
    no_resolve = any(value.lower() == "no-resolve" for value in rule_values[1:])
    return TaggedMapping(f"!{type_format[rule_type]}", rule_values[0], no_resolve)
