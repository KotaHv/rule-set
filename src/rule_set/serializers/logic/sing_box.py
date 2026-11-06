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

type SingBoxRule = dict[str, str | bool | int | list[SingBoxRule]]

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


def _serialize_logical(*, node: Node, invert: bool | None = None) -> SingBoxRule:
    """Serialize logical node to string."""
    match node:
        case Rule(rule=rule):
            entry = format_rule(rule.rule_type, rule.rule_values[0])
            if invert is not None:
                entry["invert"] = invert
            return entry

        case Logical(op=LogicalOperator.NOT, children=(child,)):
            next_invert = True if invert is None else not invert
            return _serialize_logical(node=child, invert=next_invert)

        case Logical(op=op, children=children):
            result: SingBoxRule = {
                "type": "logical",
                "rules": [_serialize_logical(node=child) for child in children],
                "mode": op.lower(),
            }
            if invert is not None:
                result["invert"] = invert
            return result


def serialize(*, tree: LogicalTree) -> SingBoxRule | None:
    try:
        return _serialize_logical(node=tree.root)
    except UnsupportedRuleTypeError as e:
        logger.error(f"rule: {surge_serialize(tree=tree)}, err: {e}")
    except SerializerError as e:
        logger.error(e)


def format_rule(rule_type: str, rule: str) -> SingBoxRule:
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
