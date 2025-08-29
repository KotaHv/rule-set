from anytree import Node
from loguru import logger

from utils import is_logical_keyword, is_logical_not, is_logical_and_or

from ..error import SerializeError, UnsupportedRuleTypeError
from .surge import serialize as surge_logical_serialize

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


def serialize(
    *, root_node: Node
) -> tuple[str, list[dict[str, str]] | dict[str, str]] | None:
    for node in [root_node, *root_node.descendants]:
        if isinstance(node.name, str):
            node.name = node.name.lower()
    try:
        logical_set, logical_type = f"{root_node.name}_set", f"!{root_node.name}"
        return logical_set, _serialize(root_node)[logical_type]
    except SerializeError as e:
        logger.error(e)
    except Exception as e:
        logger.error(
            f"rule: '{surge_logical_serialize(root_node=root_node)}', err: {e}"
        )


def _serialize(node: Node) -> dict[str, str]:
    if isinstance(node.name, tuple):
        rule = format_rule(node.name[0], node.name[1])
        return rule
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
    rule = {}
    logical_type = f"!{node.name}"
    if is_logical_not(node.name):
        rule[logical_type] = _serialize(node.children[0])
    else:
        rule[logical_type] = []
        for child_node in node.children:
            rule[logical_type].append(_serialize(child_node))
    return rule


def format_rule(rule_type: str, rule: str) -> dict[str, str]:
    rule_type = rule_type.upper()
    if rule_type not in include_type:
        raise UnsupportedRuleTypeError(rule_type)
    return {f"!{type_format[rule_type]}": rule}
