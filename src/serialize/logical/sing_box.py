from loguru import logger

from ..error import UnsupportedRuleTypeError, SerializeError
from .surge import serialize as surge_serialize
from model.logical import (
    LogicalTree,
    NotNode,
    RuleNode,
    LogicalNodeUnion,
)

type_format = {
    "domain-suffix": "domain_suffix",
    "domain-keyword": "domain_keyword",
    "domain-regex": "domain_regex",
    "ip-cidr": "ip_cidr",
    "ip-cidr6": "ip_cidr",
    "process-name": "process_name",
    "process-path": "process_path",
    "dest-port": "port",
    "src-port": "source_port",
    "src-ip": "source_ip_cidr",
    "src-ip-cidr": "source_ip_cidr",
}

include_types = [
    "query_type",
    "network",
    "domain",
    "domain_suffix",
    "domain_keyword",
    "domain_regex",
    "source_ip_cidr",
    "ip_cidr",
    "source_port",
    "source_port_range",
    "port",
    "port_range",
    "process_name",
    "process_path",
    "package_name",
    "wifi_ssid",
    "wifi_bssid",
]

protocol_types = [
    "http",
    "tls",
    "quic",
    "stun",
    "dns",
    "bittorrent",
    "dtls",
    "ssh",
    "rdp",
    "ntp",
]
protocol_types_format = {"https": "tls"}


def _serialize_logical(
    *, node: LogicalNodeUnion
) -> dict[str, list[dict[str, str]] | str]:
    """Serialize logical node to string."""
    if isinstance(node, RuleNode):
        return format_rule(node.rule.rule_type, node.rule.rule_values[0])
    if isinstance(node, NotNode):
        return _serialize_not_logical(node=node)

    else:
        rule = {"type": "logical", "rules": [], "mode": node.operator.lower()}
        for child_node in node.get_children():
            rule["rules"].append(_serialize_logical(node=child_node))
        return rule


def _serialize_not_logical(
    *, node: LogicalNodeUnion, invert: bool = True
) -> dict[str, list[dict[str, str]] | str]:
    child_node = node.child
    if isinstance(child_node, RuleNode):
        rule = format_rule(child_node.rule.rule_type, child_node.rule.rule_values[0])
        rule["invert"] = invert
        return rule
    if isinstance(child_node, NotNode):
        return _serialize_not_logical(node=child_node, invert=not invert)
    rule = {
        "type": "logical",
        "rules": [],
        "mode": child_node.operator.lower(),
        "invert": invert,
    }
    for child_node in child_node.get_children():
        rule["rules"].append(_serialize_logical(node=child_node))
    return rule


def serialize(*, tree: LogicalTree) -> dict | None:
    try:
        return _serialize_logical(node=tree.root)
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {surge_serialize(tree=tree)}, err: {e}")
    except SerializeError as e:
        logger.error(e)


def format_rule(rule_type: str, rule: str) -> dict[str, str]:
    rule_type = rule_type.lower()
    rule_type = type_format.get(rule_type, rule_type)
    if rule_type in include_types:
        if rule_type == "port":
            return {"port": int(rule)}
        return {rule_type: rule}
    if rule_type == "protocol":
        rule = rule.lower()
        rule = protocol_types_format.get(rule, rule)
        if rule in ["udp", "tcp"]:
            return {"network": rule}
        if rule in protocol_types:
            return {"protocol": rule}

    raise UnsupportedRuleTypeError(rule_type)
