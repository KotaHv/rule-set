from loguru import logger

from rule_set.errors import SerializerError, UnsupportedRuleTypeError
from rule_set.models.logical import (
    Logical,
    LogicalOperator,
    LogicalTree,
    Node,
    Rule,
)
from rule_set.models.sing_box import (
    SingBoxLeafRule,
    SingBoxLogicalRule,
    SingBoxRule,
)

from .surge import serialize as surge_serialize

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
    """Serialize logical node to SingBoxRule."""
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
            result: SingBoxLogicalRule = {
                "type": "logical",
                "rules": [_serialize_logical(node=child) for child in children],
                "mode": "and" if op is LogicalOperator.AND else "or",
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


def format_rule(rule_type: str, rule: str) -> SingBoxLeafRule:
    rule_type = rule_type.lower()
    rule_type = type_format.get(rule_type, rule_type)
    match rule_type:
        case "query_type":
            return {"query_type": rule}
        case "network":
            return {"network": rule}
        case "domain":
            return {"domain": rule}
        case "domain_suffix":
            return {"domain_suffix": rule}
        case "domain_keyword":
            return {"domain_keyword": rule}
        case "domain_regex":
            return {"domain_regex": rule}
        case "source_ip_cidr":
            return {"source_ip_cidr": rule}
        case "ip_cidr":
            return {"ip_cidr": rule}
        case "source_port":
            return {"source_port": int(rule)}
        case "source_port_range":
            return {"source_port_range": rule}
        case "port":
            return {"port": int(rule)}
        case "port_range":
            return {"port_range": rule}
        case "process_name":
            return {"process_name": rule}
        case "process_path":
            return {"process_path": rule}
        case "package_name":
            return {"package_name": rule}
        case "wifi_ssid":
            return {"wifi_ssid": rule}
        case "wifi_bssid":
            return {"wifi_bssid": rule}
        case "protocol":
            protocol = rule.lower()
            protocol = protocol_types_format.get(protocol, protocol)
            if protocol in ["udp", "tcp"]:
                return {"network": protocol}
            if protocol in protocol_types:
                return {"protocol": protocol}

            raise UnsupportedRuleTypeError(rule_type)
        case _:
            raise UnsupportedRuleTypeError(rule_type)
