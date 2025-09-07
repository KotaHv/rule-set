from loguru import logger

from rule_set.models.logical import (
    LogicalNodeUnion,
    LogicalTree,
    NotNode,
    RuleNode,
)

from ..errors import SerializerError, UnsupportedRuleTypeError
from .surge import serialize as surge_serialize

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


def _serialize_logical(*, node: LogicalNodeUnion) -> dict[str, dict[str, str | bool]]:
    if isinstance(node, RuleNode):
        return format_rule(node.rule.rule_type, node.rule.rule_values)

    rule = {}
    logical_type = f"!{node.operator.lower()}"
    if isinstance(node, NotNode):
        rule[logical_type] = {"match": _serialize_logical(node=node.child)}
    else:
        rule[logical_type] = {"match": []}
        for child in node.get_children():
            rule[logical_type]["match"].append(_serialize_logical(node=child))
    return rule


def serialize(
    *, tree: LogicalTree
) -> tuple[str, list[dict[str, str]] | dict[str, str]] | None:
    try:
        logical_type = tree.root.operator.lower()
        logical_set, logical_type = f"{logical_type}_set", f"!{logical_type}"
        return logical_set, _serialize_logical(node=tree.root)[logical_type]
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {surge_serialize(tree=tree)}, err: {e}")
    except SerializerError as e:
        logger.error(e)


def format_rule(
    rule_type: str, rule_values: list[str]
) -> dict[str, dict[str, str | bool]]:
    rule_type = rule_type.upper()
    if rule_type not in include_type:
        raise UnsupportedRuleTypeError(rule_type)
    rule = {f"!{type_format[rule_type]}": {"match": rule_values[0]}}
    for value in rule_values[1:]:
        if value.lower() == "no-resolve":
            rule["match"]["no-resolve"] = True
            break

    return rule
